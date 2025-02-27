#!/usr/bin/env python3

import argparse
import sys

parser = argparse.ArgumentParser(
    description="This program converts Excellon .drl files into G-Code for a CNC machine. Originally by Franco Lanza."
)
parser.add_argument("drlfile", metavar="DRLFILE", nargs=1, help="Excellon .drl file")
parser.add_argument(
    "--spindle-speed", help="Set the spindle speed in RPM", type=float, default=32000
)
parser.add_argument(
    "--xy-move-speed",
    help="Set the X/Y travel move speed in mm/min",
    type=float,
    default=3000,
)
parser.add_argument(
    "--z-move-speed",
    help="Set the Z travel move speed in mm/min",
    type=float,
    default=300,
)
parser.add_argument(
    "--drill-move-speed",
    help="Set the Z drilling speed in mm/min",
    type=float,
    default=100,
)
parser.add_argument(
    "--drill-depth",
    help="Set the distance to drill below z=0 (positive, larger values go deeper)",
    type=float,
    default=2,
)
parser.add_argument(
    "--safe-height",
    help="Set the Z coordinate to use for rapid moves",
    type=float,
    default=25,
)
parser.add_argument(
    "-s",
    "--single-file",
    help="Do not split drill files on separate gcodes by diameters",
    action="store_true",
)

parser.add_argument(
    "-o",
    "--offset",
    help="Offset all coordinates, X Y",
    nargs=2,
    type=float,
    default=[0, 0],
)

args = parser.parse_args()
print(args)
header = (
    """; Produced by drl2gcode.py originally by Franco Lanza

; select absolute coordinate system
G90
; metric
G21
; G61 exact path mode was requested but not implemented
; start spindle
M3 S"""
    + str(args.spindle_speed)
    + """
"""
)

footer = (
    """
; stop spindle
M5
; go to safe height
G1 Z"""
    + str(args.safe_height)
    + """ F30000
; program ends
M2
"""
)


tools = {}
tsel = "1"

newl3 = "".join(["G1 F", str(args.z_move_speed), " Z0.2"])
newl4 = "".join(["G1 F", str(args.drill_move_speed), " Z-", str(args.drill_depth)])


with open(args.drlfile[0]) as fp:
    line = fp.readline()
    while line:
        line = fp.readline()
        if line.startswith("T") and "C" in line:
            tnum = line.split("C")[0][1:]
            diameter = "{:.2f}".format(float(line.split("C")[1]))
            tools[tnum] = {
                "diameter": diameter,
                "file": "".join(
                    [
                        args.drlfile[0][:-4],
                        "_T",
                        tnum.rjust(2, "0"),
                        "_",
                        diameter,
                        "mm",
                        ".gcode",
                    ]
                ),
                "output": "".join(
                    [
                        "\n\n; T",
                        tnum,
                        " Diameter: ",
                        diameter,
                        "mm",
                        "\n",
                        "M06\n",
                        "M117 insert tool with diameter: ",
                        diameter,
                        "mm",
                        "\n",
                    ]
                ),
                "first": True,
            }
        elif line.startswith("T"):
            tsel = line[1:].rstrip("\r\n")
        elif line.startswith("X") and tsel != "0":
            newl1 = "".join(
                ["G1 F", str(args.z_move_speed), " Z", str(args.safe_height)]
            )
            x = float(line.split("Y")[0].strip("X")) + args.offset[0]
            y = float(line.split("Y")[1].strip("\r\n")) + args.offset[1]
            # print(x, y)
            newl2 = "".join(
                [
                    "G1 F",
                    str(args.xy_move_speed),
                    " X",
                    str(x),
                    " Y",
                    str(y),
                ]
            )

            tools[tsel]["output"] += "\n".join([newl1, newl2, newl3, newl4, ""])

if args.single_file:
    out_file = "".join([args.drlfile[0][:-4], "_Tall.gcode"])
    output = header
    for t in tools:
        output += tools[t]["output"]
    output += footer
    with open(out_file, "w") as f:
        f.write(output)
    print("Writtent to %s" % out_file)

else:
    for t in tools:
        tools[t]["output"] = "".join([header, tools[t]["output"], footer])
        print("writing", tools[t]["file"])
        with open(tools[t]["file"], "w") as f:
            f.write(tools[t]["output"])
