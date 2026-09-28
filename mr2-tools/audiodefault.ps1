# audiodefault.ps1 - set the default playback device and hide/disable an endpoint
# (same calls the Sound control panel makes, via the undocumented IPolicyConfig).
#   .\audiodefault.ps1 -Default <endpointId>        -> default for console+multimedia+communications
#   .\audiodefault.ps1 -Disable <endpointId>        -> disable endpoint (like Sound panel > Disable)
#   .\audiodefault.ps1 -Enable  <endpointId>        -> re-enable it
param([string]$Default = "", [string]$Disable = "", [string]$Enable = "")

Add-Type @'
using System; using System.Runtime.InteropServices;
[ComImport, Guid("870AF99C-171D-4F9E-AF0D-E63DF40C2BC9")] public class PolicyConfigClient { }
[ComImport, Guid("F8679F50-850A-41CF-9C72-430F290290C8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IPolicyConfig {
  int GetMixFormat(); int GetDeviceFormat(); int ResetDeviceFormat(); int SetDeviceFormat();
  int GetProcessingPeriod(); int SetProcessingPeriod(); int GetShareMode(); int SetShareMode();
  int GetPropertyValue(); int SetPropertyValue();
  [PreserveSig] int SetDefaultEndpoint([MarshalAs(UnmanagedType.LPWStr)] string id, int role);
  [PreserveSig] int SetEndpointVisibility([MarshalAs(UnmanagedType.LPWStr)] string id, int visible);
}
public static class AD {
  static IPolicyConfig P() { return (IPolicyConfig)new PolicyConfigClient(); }
  public static string SetDefault(string id) { var p = P(); return p.SetDefaultEndpoint(id,0)+","+p.SetDefaultEndpoint(id,1)+","+p.SetDefaultEndpoint(id,2); }
  public static int Visible(string id, bool v) { return P().SetEndpointVisibility(id, v ? 1 : 0); }
}
'@
if ($Default) { "set default $Default -> hr=" + [AD]::SetDefault($Default) }
if ($Disable) { "disable $Disable -> hr=" + [AD]::Visible($Disable, $false) }
if ($Enable)  { "enable $Enable -> hr="  + [AD]::Visible($Enable, $true) }
