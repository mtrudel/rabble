DefinitionBlock ("", "SSDT", 5, "NVIDIA", "S0IX", 0x00000001)
{
    External (S0ID, FieldUnitObj)
    External (_SB_.PEPD, DeviceObj)

    // Force S0ID=1 so that PEPD._DSM function 1 returns a populated LPS0
    // device constraint list instead of an empty package. The BIOS sets
    // S0ID=0 on this desktop (no Modern Standby support in firmware), which
    // prevents the kernel's LPS0 path from coordinating S0ix device entry.
    // PEPD has no _INI in the DSDT, so this adds a new method rather than
    // overriding an existing one (SSDTs cannot override existing DSDT methods).
    Scope (\_SB.PEPD)
    {
        Method (_INI, 0, NotSerialized)
        {
            S0ID = One
        }
    }
}
