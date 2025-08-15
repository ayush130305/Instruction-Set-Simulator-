# Instruction Set Simulator (ISS) - Python + Tkinter

## Overview
This is a graphical Instruction Set Simulator for an 8-bit CPU architecture, built using Python's Tkinter library.  
The simulator allows you to:
- Write and execute **assembly-like instructions**.
- View **registers, memory, special registers, and buses** in real time.
- Run **single-line, multi-line, or line-by-line** execution.
- Validate instructions before execution.
- Track **control signal history**.
- Visualize the **Von Neumann architecture buses** (Address, Data, Control).
- See the **FLAGS register** update (Z, N, C, V).

The simulator is designed for **educational purposes** to help students and hobbyists understand basic CPU operations, instruction cycles, and memory/register interactions.

---

## Features
- **8-bit CPU emulation** (values range from 0–255).
- **Instruction set support**:
  - `LOAD` – Load a value into a register.
  - `STORE` – Store register value into memory.
  - `MOVE` – Move value from one register to another.
  - `ADD`, `SUB`, `MUL` – Support both **two-operand** and **three-operand** versions.
  - `INC`, `DEC` – Increment/Decrement register value.
- **Memory**: 8x8 grid view (64 locations, 0x00 to 0x3F).
- **Registers**: R0–R7 general-purpose registers.
- **Special Registers**:
  - `PC` – Program Counter
  - `IR` – Instruction Register
  - `MAR` – Memory Address Register
  - `MDR` – Memory Data Register
  - `FLAGS` – Z (Zero), N (Negative), C (Carry), V (Overflow)
- **Buses**:
  - Address Bus
  - Data Bus
  - Control Bus
- **Execution Modes**:
  - `Verify` – Checks if all instructions are valid before running.
  - `Step` – Executes all instructions in the text box at once.
  - `Next` – Executes one instruction at a time (line-by-line).
  - `Reset` – Resets CPU state, memory, and instruction history.
- **Control Signals Panel**:
  - Displays recent instruction history.

---

## Installation
### Requirements
- Python 3.x
- Tkinter (usually included with Python)
  
### Clone Repository
```bash
git clone https://github.com/yourusername/instruction-set-simulator.git
cd instruction-set-simulator
