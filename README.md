# 8-Bit CPU Instruction Set Simulator

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![GUI](https://img.shields.io/badge/GUI-Tkinter-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

A comprehensive, graphical **Instruction Set Simulator** for an 8-bit CPU architecture based on the **Von Neumann model**. 

Built with Python and Tkinter, this tool is designed for educational purposes to visualize how a processor fetches, decodes, and executes instructions, manages memory, and handles control signals.


## 🚀 Key Features

* **Real-time Visualization:** Watch values change in General Purpose Registers (R0-R7), Memory (8x8 Matrix), and System Buses (Address, Data, Control).
* **Visual Data Flow:** System buses light up to show data movement during execution.
* **Instruction Pipeline:** Tracks Program Counter (PC), Instruction Register (IR), and Memory Address/Data Registers (MAR/MDR).
* **Flags Register:** dynamic updates for Zero (Z), Negative (N), Carry (C), and Overflow (V) flags.
* **Code Editor:**
    * Syntax Highlighting (Keywords, Registers, Numbers, Comments).
    * Line number tracking.
* **Execution Modes:**
    * **Step All:** Batch execution.
    * **Next:** Animated line-by-line debugging with variable speed control.
    * **Undo/Redo:** Go back in time to debug state changes.
* **Dark Mode:** Toggle between Light and Dark themes.

## 🛠 Architecture Overview

* **Data Width:** 8-bit (Values 0-255).
* **Address Space:** 64 Bytes (0x00 to 0x3F).
* **Registers:** 8 General Purpose (R0-R7).
* **Addressing Modes:** Immediate, Register Direct, Absolute Direct.

## 📝 Instruction Set

The simulator supports a custom assembly-like syntax. Operands must be separated by commas.

| Category | Opcode | Syntax | Description |
| :--- | :--- | :--- | :--- |
| **Data Transfer** | `LOAD` | `LOAD Rx, val` | Load immediate value (0-255) into register. |
| | `STORE` | `STORE Rx, addr` | Store register value into memory address. |
| | `MOV` | `MOV Rd, Rs` | Copy value from Source to Destination register. |
| **Arithmetic** | `ADD` | `ADD Rd, Rs1, Rs2` | Add Rs1 and Rs2, store in Rd (or `ADD Rx, Ry`). |
| | `SUB` | `SUB Rd, Rs1, Rs2` | Subtract Rs2 from Rs1, store in Rd (or `SUB Rx, Ry`). |
| | `MUL` | `MUL Rd, Rs1, Rs2` | Multiply Rs1 and Rs2, store in Rd (or `MUL Rx, Ry`). |
| | `INC` | `INC Rx` | Increment register by 1. |
| | `DEC` | `DEC Rx` | Decrement register by 1. |
| **Control Flow** | `CMP` | `CMP Rx, Ry` | Compare registers (updates FLAGS only). |
| | `JMP` | `JMP line` | Unconditional jump to line number. |
| | `JZ` / `JNZ` | `JZ line` | Jump if Zero / Jump if Not Zero. |
| | `JC` / `JN` | `JC line` | Jump if Carry / Jump if Negative. |
| **Misc** | `NOP` | `NOP` | No Operation. |
| **Comments** | `;` or `#` | `; Comment` | Ignored by the assembler. |

## 💻 Installation & Usage

### Prerequisites
* Python 3.x installed.
* Tkinter (usually included with standard Python installations).

### Running the Simulator
1.  Clone the repository:
    ```bash
    git clone [https://github.com/yourusername/cpu-simulator.git](https://github.com/yourusername/cpu-simulator.git)
    ```
2.  Navigate to the directory:
    ```bash
    cd cpu-simulator
    ```
3.  Run the application:
    ```bash
    python main.py
    ```

## 🧪 Example Program

Copy and paste this into the simulator to test the functionality. This program initializes values, performs addition, and runs a loop using a jump instruction.

```asm
; Initialize values
LOAD R0, 10      
STORE R0, 10    ; Store 10 at address 10
LOAD R1, 20      
STORE R1, 11    ; Store 20 at address 11

; Arithmetic
LOAD R3, 10      
LOAD R4, 11      
ADD R5, R3, R4  ; R5 = 10 + 11 = 21
STORE R5, 37    ; Store result

; Loop Example
LOAD R6, 0      ; Counter
LOAD R7, 5      ; Limit

INC R6          ; Increment Counter
CMP R6, R7      ; Compare Counter with Limit
JNZ 14          ; Jump back to INC if not equal (Line 14)
STORE R6, 10    ; Store final count
