DefinitionBlock ("", "SSDT", 5, "NVIDIA", "RTND3", 0x00000003)
{
    External (_SB_.PC00.PEG1, DeviceObj)
    External (_SB_.PC00.PEG1.PEGP, DeviceObj)

    Scope (\_SB.PC00.PEG1)
    {
        PowerResource (PGPR, 0, 0)
        {
            Name (_STA, One)
            Method (_ON, 0, Serialized) {}
            Method (_OFF, 0, Serialized) {}
        }

        Name (_PR3, Package (0x01) { \_SB.PC00.PEG1.PGPR })
    }

    Scope (\_SB.PC00.PEG1.PEGP)
    {
        Name (_PR0, Package (0x01) { \_SB.PC00.PEG1.PGPR })
        Name (_PR3, Package (0x01) { \_SB.PC00.PEG1.PGPR })
    }
}
