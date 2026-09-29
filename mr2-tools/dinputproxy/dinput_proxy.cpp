// dinput.dll proxy for Moto Racer 2 (32-bit). Sits in the game folder; forwards everything to the
// real system dinput.dll, except:
//  1. DualSense (VID 054C) buttons are re-ordered to the Xbox/"button 1 = OK" convention the 1998
//     game expects:  out1 = Cross, out2 = Circle, out3 = Square, out4 = Triangle (rest unchanged).
//  2. Test injection: if a shared-memory block "Local\MR2PadInject" exists, its button mask / POV
//     are OR'd into every joystick read - lets tools press virtual pad buttons for automated tests.
//  3. Logs device creation and read style to %TEMP%\mr2-dinput.log.
// Build (x86): cl /LD /O2 /EHsc dinput_proxy.cpp /link /DEF:dinput.def /OUT:dinput.dll user32.lib dxguid.lib
#define DIRECTINPUT_VERSION 0x0500
#include <windows.h>
#include <dinput.h>
#include <stdio.h>

static HMODULE g_real;
typedef HRESULT (WINAPI *PFN_DICreateA)(HINSTANCE, DWORD, LPDIRECTINPUTA *, LPUNKNOWN);

static void Log(const char *fmt, ...)
{
    char path[MAX_PATH]; GetTempPathA(MAX_PATH, path); lstrcatA(path, "mr2-dinput.log");
    FILE *f = fopen(path, "a"); if (!f) return;
    SYSTEMTIME t; GetLocalTime(&t); fprintf(f, "%02d:%02d:%02d.%03d ", t.wHour, t.wMinute, t.wSecond, t.wMilliseconds);
    va_list a; va_start(a, fmt); vfprintf(f, fmt, a); va_end(a); fputc('\n', f); fclose(f);
}

struct Inject { DWORD magic; DWORD buttons; LONG pov; };   // magic = 'MR2P'
static Inject *InjectBlock()
{
    static HANDLE h; static Inject *p;
    if (!p) {
        h = OpenFileMappingA(FILE_MAP_READ, FALSE, "Local\\MR2PadInject");
        if (h) p = (Inject *)MapViewOfFile(h, FILE_MAP_READ, 0, 0, sizeof(Inject));
    }
    return (p && p->magic == 0x5032524D) ? p : NULL;
}

// DualSense physical (DirectInput 0-based): 0 Square 1 Cross 2 Circle 3 Triangle
// out[i] = in[kMap[i]]  ->  out0 = Cross, out1 = Circle, out2 = Square, out3 = Triangle
static const int kMap[4] = { 1, 2, 0, 3 };
static const int kInv[4] = { 2, 0, 1, 3 };   // physical p -> output index

class ProxyDevice : public IDirectInputDevice2A
{
    LONG m_ref; IDirectInputDevice2A *m_real; bool m_isJoy, m_ds; DWORD m_fmtSize; int m_logged;
public:
    ProxyDevice(IDirectInputDevice2A *real, bool isJoy, bool ds) : m_ref(1), m_real(real), m_isJoy(isJoy), m_ds(ds), m_fmtSize(0), m_logged(0) {}

    DWORD m_lastRaw = 0xFFFFFFFF, m_lastPov = 0xFFFFFFFE; int m_changes = 0;
    void Fix(DWORD cb, LPVOID data)
    {
        if (!m_isJoy || !data || cb < sizeof(DIJOYSTATE)) return;
        DIJOYSTATE *js = (DIJOYSTATE *)data;
        DWORD raw = 0; for (int b = 0; b < 32; b++) if (js->rgbButtons[b] & 0x80) raw |= 1u << b;
        if ((raw != m_lastRaw || js->rgdwPOV[0] != m_lastPov) && m_changes < 200) {
            Log("joy raw buttons=0x%08lX pov=%ld x=%ld y=%ld z=%ld rx=%ld ry=%ld rz=%ld", raw, (LONG)js->rgdwPOV[0], js->lX, js->lY, js->lZ, js->lRx, js->lRy, js->lRz);
            m_lastRaw = raw; m_lastPov = js->rgdwPOV[0]; m_changes++;
        }
        if (m_ds) { BYTE in[4]; for (int i = 0; i < 4; i++) in[i] = js->rgbButtons[i]; for (int i = 0; i < 4; i++) js->rgbButtons[i] = in[kMap[i]]; }
        // Hide game button 2 (Circle / B) and the D-pad from the game: MotoRacer2Launcher's helper turns
        // them into Esc / arrow keys, so a native reaction as well would count every press twice (#16).
        // Neither is used by any race binding.
        js->rgbButtons[1] = 0; js->rgdwPOV[0] = 0xFFFFFFFF;
        if (Inject *inj = InjectBlock()) {
            for (int b = 0; b < 32; b++) if (inj->buttons & (1u << b)) js->rgbButtons[b] = 0x80;
            if (inj->pov != -1) js->rgdwPOV[0] = (DWORD)inj->pov;
        }
    }

    // IUnknown
    STDMETHOD(QueryInterface)(REFIID riid, LPVOID *out)
    {
        if (riid == IID_IUnknown || riid == IID_IDirectInputDeviceA || riid == IID_IDirectInputDevice2A) { AddRef(); *out = this; return S_OK; }
        return m_real->QueryInterface(riid, out);
    }
    STDMETHOD_(ULONG, AddRef)() { return InterlockedIncrement(&m_ref); }
    STDMETHOD_(ULONG, Release)() { LONG r = InterlockedDecrement(&m_ref); if (!r) { m_real->Release(); delete this; } return r; }
    // IDirectInputDeviceA
    STDMETHOD(GetCapabilities)(LPDIDEVCAPS c) { return m_real->GetCapabilities(c); }
    STDMETHOD(EnumObjects)(LPDIENUMDEVICEOBJECTSCALLBACKA cb, LPVOID r, DWORD f) { return m_real->EnumObjects(cb, r, f); }
    STDMETHOD(GetProperty)(REFGUID g, LPDIPROPHEADER p) { return m_real->GetProperty(g, p); }
    STDMETHOD(SetProperty)(REFGUID g, LPCDIPROPHEADER p) { return m_real->SetProperty(g, p); }
    STDMETHOD(Acquire)() { return m_real->Acquire(); }
    STDMETHOD(Unacquire)() { return m_real->Unacquire(); }
    STDMETHOD(GetDeviceState)(DWORD cb, LPVOID d)
    {
        HRESULT hr = m_real->GetDeviceState(cb, d);
        if (m_isJoy && m_logged < 1) { Log("joy GetDeviceState cb=%lu hr=0x%08lX", cb, hr); m_logged++; }
        if (SUCCEEDED(hr)) Fix(cb, d);
        return hr;
    }
    STDMETHOD(GetDeviceData)(DWORD cb, LPDIDEVICEOBJECTDATA od, LPDWORD n, DWORD f)
    {
        HRESULT hr = m_real->GetDeviceData(cb, od, n, f);
        if (m_isJoy && m_logged < 2) { Log("joy GetDeviceData (buffered) used"); m_logged = 2; }
        if (SUCCEEDED(hr) && m_isJoy && m_ds && od && n)
            for (DWORD i = 0; i < *n; i++) {
                DIDEVICEOBJECTDATA *e = (DIDEVICEOBJECTDATA *)((BYTE *)od + i * cb);
                DWORD b = e->dwOfs - DIJOFS_BUTTON0;
                if (e->dwOfs >= DIJOFS_BUTTON0 && b < 4) e->dwOfs = DIJOFS_BUTTON(kInv[b]);
            }
        return hr;
    }
    STDMETHOD(SetDataFormat)(LPCDIDATAFORMAT f) { if (f) m_fmtSize = f->dwDataSize; if (m_isJoy) Log("joy SetDataFormat size=%lu", m_fmtSize); return m_real->SetDataFormat(f); }
    STDMETHOD(SetEventNotification)(HANDLE h) { return m_real->SetEventNotification(h); }
    STDMETHOD(SetCooperativeLevel)(HWND w, DWORD f) { return m_real->SetCooperativeLevel(w, f); }
    STDMETHOD(GetObjectInfo)(LPDIDEVICEOBJECTINSTANCEA o, DWORD a, DWORD b) { return m_real->GetObjectInfo(o, a, b); }
    STDMETHOD(GetDeviceInfo)(LPDIDEVICEINSTANCEA i) { return m_real->GetDeviceInfo(i); }
    STDMETHOD(RunControlPanel)(HWND w, DWORD f) { return m_real->RunControlPanel(w, f); }
    STDMETHOD(Initialize)(HINSTANCE i, DWORD v, REFGUID g) { return m_real->Initialize(i, v, g); }
    // IDirectInputDevice2A
    STDMETHOD(CreateEffect)(REFGUID g, LPCDIEFFECT e, LPDIRECTINPUTEFFECT *o, LPUNKNOWN u) { return m_real->CreateEffect(g, e, o, u); }
    STDMETHOD(EnumEffects)(LPDIENUMEFFECTSCALLBACKA cb, LPVOID r, DWORD t) { return m_real->EnumEffects(cb, r, t); }
    STDMETHOD(GetEffectInfo)(LPDIEFFECTINFOA e, REFGUID g) { return m_real->GetEffectInfo(e, g); }
    STDMETHOD(GetForceFeedbackState)(LPDWORD s) { return m_real->GetForceFeedbackState(s); }
    STDMETHOD(SendForceFeedbackCommand)(DWORD c) { return m_real->SendForceFeedbackCommand(c); }
    STDMETHOD(EnumCreatedEffectObjects)(LPDIENUMCREATEDEFFECTOBJECTSCALLBACK cb, LPVOID r, DWORD f) { return m_real->EnumCreatedEffectObjects(cb, r, f); }
    STDMETHOD(Escape)(LPDIEFFESCAPE e) { return m_real->Escape(e); }
    STDMETHOD(Poll)() { return m_real->Poll(); }
    STDMETHOD(SendDeviceData)(DWORD cb, LPCDIDEVICEOBJECTDATA d, LPDWORD n, DWORD f) { return m_real->SendDeviceData(cb, d, n, f); }
};

class ProxyDI : public IDirectInput2A
{
    LONG m_ref; IDirectInput2A *m_real;
public:
    ProxyDI(IDirectInput2A *real) : m_ref(1), m_real(real) {}
    STDMETHOD(QueryInterface)(REFIID riid, LPVOID *out)
    {
        if (riid == IID_IUnknown || riid == IID_IDirectInputA || riid == IID_IDirectInput2A) { AddRef(); *out = this; return S_OK; }
        return m_real->QueryInterface(riid, out);
    }
    STDMETHOD_(ULONG, AddRef)() { return InterlockedIncrement(&m_ref); }
    STDMETHOD_(ULONG, Release)() { LONG r = InterlockedDecrement(&m_ref); if (!r) { m_real->Release(); delete this; } return r; }
    STDMETHOD(CreateDevice)(REFGUID g, LPDIRECTINPUTDEVICEA *out, LPUNKNOWN u)
    {
        LPDIRECTINPUTDEVICEA dev = NULL;
        HRESULT hr = m_real->CreateDevice(g, &dev, u);
        if (FAILED(hr) || !dev) return hr;
        IDirectInputDevice2A *dev2 = NULL;
        if (FAILED(dev->QueryInterface(IID_IDirectInputDevice2A, (void **)&dev2)) || !dev2) { *out = dev; return hr; }
        dev->Release();
        DIDEVCAPS caps = { sizeof(caps) }; dev2->GetCapabilities(&caps);
        BYTE type = GET_DIDEVICE_TYPE(caps.dwDevType);
        bool isJoy = type == DIDEVTYPE_JOYSTICK;
        bool ds = false;
        if (isJoy) {
            // HID devices: guidProduct.Data1 = MAKELONG(VID, PID)
            DIDEVICEINSTANCEA di = { sizeof(di) }; dev2->GetDeviceInfo(&di);
            ds = LOWORD(di.guidProduct.Data1) == 0x054C;
            Log("CreateDevice joystick product=0x%08lX name=\"%s\" dualsense_remap=%d buttons=%lu", di.guidProduct.Data1, di.tszProductName, ds, caps.dwButtons);
        }
        *out = (LPDIRECTINPUTDEVICEA)new ProxyDevice(dev2, isJoy, ds);
        return hr;
    }
    STDMETHOD(EnumDevices)(DWORD t, LPDIENUMDEVICESCALLBACKA cb, LPVOID r, DWORD f) { return m_real->EnumDevices(t, cb, r, f); }
    STDMETHOD(GetDeviceStatus)(REFGUID g) { return m_real->GetDeviceStatus(g); }
    STDMETHOD(RunControlPanel)(HWND w, DWORD f) { return m_real->RunControlPanel(w, f); }
    STDMETHOD(Initialize)(HINSTANCE i, DWORD v) { return m_real->Initialize(i, v); }
    STDMETHOD(FindDevice)(REFGUID g, LPCSTR n, LPGUID o) { return m_real->FindDevice(g, n, o); }
};

static bool LoadReal()
{
    if (g_real) return true;
    char path[MAX_PATH]; GetSystemDirectoryA(path, MAX_PATH); lstrcatA(path, "\\dinput.dll");   // SysWOW64 for x86
    g_real = LoadLibraryA(path);
    return g_real != NULL;
}

extern "C" HRESULT WINAPI Proxy_DirectInputCreateA(HINSTANCE inst, DWORD ver, LPDIRECTINPUTA *out, LPUNKNOWN outer)
{
    if (!LoadReal()) return DIERR_GENERIC;
    PFN_DICreateA create = (PFN_DICreateA)GetProcAddress(g_real, "DirectInputCreateA");
    LPDIRECTINPUTA di = NULL;
    HRESULT hr = create(inst, ver, &di, outer);
    Log("DirectInputCreateA ver=0x%04lX hr=0x%08lX", ver, hr);
    if (FAILED(hr) || !di) return hr;
    IDirectInput2A *di2 = NULL;
    if (FAILED(di->QueryInterface(IID_IDirectInput2A, (void **)&di2)) || !di2) { *out = di; return hr; }
    di->Release();
    *out = (LPDIRECTINPUTA)new ProxyDI(di2);
    return hr;
}

// Everything else goes straight to the real DLL.
template <class F> static F Real(const char *name) { return LoadReal() ? (F)GetProcAddress(g_real, name) : NULL; }
extern "C" HRESULT WINAPI Proxy_DirectInputCreateW(HINSTANCE i, DWORD v, LPDIRECTINPUTW *o, LPUNKNOWN u)
{ typedef HRESULT (WINAPI *F)(HINSTANCE, DWORD, LPDIRECTINPUTW *, LPUNKNOWN); F f = Real<F>("DirectInputCreateW"); return f ? f(i, v, o, u) : DIERR_GENERIC; }
extern "C" HRESULT WINAPI Proxy_DirectInputCreateEx(HINSTANCE i, DWORD v, REFIID r, LPVOID *o, LPUNKNOWN u)
{ typedef HRESULT (WINAPI *F)(HINSTANCE, DWORD, REFIID, LPVOID *, LPUNKNOWN); F f = Real<F>("DirectInputCreateEx"); return f ? f(i, v, r, o, u) : DIERR_GENERIC; }
extern "C" HRESULT WINAPI Proxy_DllCanUnloadNow() { typedef HRESULT (WINAPI *F)(); F f = Real<F>("DllCanUnloadNow"); return f ? f() : S_FALSE; }
extern "C" HRESULT WINAPI Proxy_DllGetClassObject(REFCLSID c, REFIID r, LPVOID *o)
{ typedef HRESULT (WINAPI *F)(REFCLSID, REFIID, LPVOID *); F f = Real<F>("DllGetClassObject"); return f ? f(c, r, o) : CLASS_E_CLASSNOTAVAILABLE; }
extern "C" HRESULT WINAPI Proxy_DllRegisterServer() { typedef HRESULT (WINAPI *F)(); F f = Real<F>("DllRegisterServer"); return f ? f() : E_FAIL; }
extern "C" HRESULT WINAPI Proxy_DllUnregisterServer() { typedef HRESULT (WINAPI *F)(); F f = Real<F>("DllUnregisterServer"); return f ? f() : E_FAIL; }
