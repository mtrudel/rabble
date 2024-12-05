# Rabble

Rabble is our home server / gaming PC. My goal was to have a machine that could
take over the burden of running the [various
things](https://github.com/mtrudel/pibox) we run around the house, and also to
act as a couch gaming PC with enough oomph to play demanding games (MSFS 2024,
mostly). Some stuff about it:

* It runs multiple VMs on a [Proxmox](https://www.proxmox.com/) host
* There's a Windows VM ('broffina') for gaming, which accesses the GPU via PCI
  passthrough ('VFIO'). [Benchmarks](https://browser.geekbench.com/user/522804)
  place it around 95-98% of bare metal performance
* The primary Linux VM ('blathers') is a work in progress, and will be bringing
  over almost all of the work in my [pibox](https://github.com/mtrudel/pibox)
  project
* We have it set up for couch gaming, with some extra provision for
  auto-switching the TV and optimized power consumption when the Windows VM is
  off (which is most of the time)
* It's Animal Crossing themed! When we were putting together the [part
  list](https://ca.pcpartpicker.com/b/nVJfrH), we
  noticed that the palette looked a lot like the colours in ACNH, so we doubled down
  with some fun decorating (more below), and used the names of our
  family island ('rabble') as the host OS hostname, and our favorite villagers
  as guest hostnames

This repo is a collection of notes around the planning, building, configuration
and maintenance of the machine, mostly for my own records but also as a source
if others want to build a similar setup.

# Hardware Build

I spent a little less than a month putting together the [part
list](https://ca.pcpartpicker.com/b/nVJfrH), focusing on
a high-end-but-still-cost-conscious approach that I later found out mapped
almost perfectly onto the [Logical Increments 'outstanding'
tier](https://www.logicalincrements.com).

Not much to say about this; it's a pretty standard PC (despite the absurd case)
and goes together without any real fuss. All of the parts other than the CPU
cooler would port over to any standard SFF case if you're looking for something
more conventional

## Decorating

TBD

# BIOS

TBD

# Host OS Install

TBD

# Linux Guest Install

TBD

# Burn In / Benchmarking

TBD

# Operational Tasks

TBD
