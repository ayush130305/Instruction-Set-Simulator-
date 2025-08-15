import tkinter as tk
from tkinter import messagebox

# === CPU STATE ===
registers = [0] * 8  # R0 to R7
memory = [0] * 64    # 4x7 memory grid
special_registers = {
    'PC': 0,
    'IR': '',
    'MAR': 0,
    'MDR': 0,
    'FLAGS': {'Z': 0, 'N': 0, 'C': 0, 'V': 0}
}
instruction_history = []  # 2x4 control section
current_line = 0

# === Instruction Execution Engine ===
def execute_instruction(instruction):
    try:
        tokens = instruction.strip().split()
        if len(tokens) < 2:
            return

        op = tokens[0].upper()
        operands = []
        if len(tokens) > 1:
            operands = [operand.strip() for operand in ' '.join(tokens[1:]).split(',')]

        if op == 'LOAD':
            if len(operands) == 2:
                reg = int(operands[0][1])
                value = int(operands[1], 0) % 256
                special_registers['MAR'] = special_registers['PC']
                special_registers['MDR'] = value
                registers[reg] = value % 256
            else:
                raise ValueError(f"'{op}' requires 2 operands")

        elif op == 'STORE':
            if len(operands) == 2:
                reg = int(operands[0][1])
                address = int(operands[1])
                value = registers[reg] % 256
                memory[address] = value
                special_registers['MAR'] = address
                special_registers['MDR'] = value
            else:
                raise ValueError(f"'{op}' requires 2 operands")

        elif op == 'MOVE':
            if len(operands) == 2:
                reg = int(operands[0][1])
                src_str = operands[1]
                if src_str.startswith('R') and src_str[1:].isdigit():
                    src = int(src_str[1:])
                    registers[reg] = registers[src] % 256
                else:
                    raise ValueError(f"Invalid source register: {src_str}")
            else:
                raise ValueError(f"'{op}' requires 2 operands")

        elif op in ['ADD', 'SUB', 'MUL']:
            if len(operands) == 2:
                reg = int(operands[0][1])
                src = int(operands[1][1])
                if op == 'ADD':
                    registers[reg] = (registers[reg] + registers[src]) % 256
                elif op == 'SUB':
                    registers[reg] = (registers[reg] - registers[src]) % 256
                elif op == 'MUL':
                    registers[reg] = (registers[reg] * registers[src]) % 256
            elif len(operands) == 3:
                dest = int(operands[0][1])
                src1 = int(operands[1][1])
                src2 = int(operands[2][1])
                if op == 'ADD':
                    registers[dest] = (registers[src1] + registers[src2]) % 256
                elif op == 'SUB':
                    registers[dest] = (registers[src1] - registers[src2]) % 256
                elif op == 'MUL':
                    registers[dest] = (registers[src1] * registers[src2]) % 256
            else:
                raise ValueError(f"'{op}' requires 2 or 3 operands")

        elif op == 'INC':
            if len(operands) == 1:
                reg = int(operands[0][1])
                registers[reg] = (registers[reg] + 1) % 256
            else:
                raise ValueError(f"'{op}' requires 1 operand")

        elif op == 'DEC':
            if len(operands) == 1:
                reg = int(operands[0][1])
                registers[reg] = (registers[reg] - 1) % 256
            else:
                raise ValueError(f"'{op}' requires 1 operand")

        special_registers['IR'] = instruction
        special_registers['PC'] += 1

    except Exception as e:
        messagebox.showerror("Execution Error", str(e))

# === GUI Update Functions ===
def update_gui():
    for i in range(8):
        register_labels[i]["text"] = str(registers[i])
    for i in range(len(memory)):
        memory_labels[i]["text"] = str(memory[i])
    # Update special registers except FLAGS
    for k in special_registers:
        if k == 'FLAGS':
            continue
        special_labels[k]["text"] = str(special_registers[k])
    # Update FLAGS register display
    flags_text = ' '.join(f"{k}:{v}" for k, v in special_registers['FLAGS'].items())
    special_labels['FLAGS']["text"] = flags_text

    # Clear existing control labels
    for widget in control_box.winfo_children():
        widget.destroy()
    control_labels.clear()

    # Recreate control labels based on instruction_history
    rows = 2
    cols = 4
    max_labels = rows * cols
    display_history = instruction_history[-max_labels:]
    for i in range(rows):
        control_box.grid_rowconfigure(i, weight=1)
    for j in range(cols):
        control_box.grid_columnconfigure(j, weight=1)

    for idx, instr in enumerate(display_history):
        row = idx // cols
        col = idx % cols
        lbl = tk.Label(control_box, text=instr, width=10, relief="sunken", anchor='w')
        lbl.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
        control_labels.append(lbl)

    bus_labels['Address Bus']["text"] = f"Address Bus: {special_registers.get('MAR', '')}"
    bus_labels['Data Bus']["text"] = f"Data Bus: {special_registers.get('MDR', '')}"
    bus_labels['Control Bus']["text"] = f"Control Bus: PC={special_registers.get('PC', '')} IR={special_registers.get('IR', '')}"

def on_step():
    global instruction_history, current_line
    instructions = instruction_entry.get("1.0", tk.END).strip().split('\n')
    for instruction in instructions:
        if instruction.strip():
            instruction_history.append(instruction.strip())
            execute_instruction(instruction)
    update_gui()

# === Execute next instruction line-by-line ===
def on_next():
    global instruction_history, current_line
    instructions = instruction_entry.get("1.0", tk.END).strip().split('\n')
    if current_line < len(instructions):
        instruction = instructions[current_line].strip()
        if instruction:
            instruction_history.append(instruction)
            execute_instruction(instruction)
            update_gui()
        current_line += 1

def on_reset():
    global registers, memory, special_registers, instruction_history, current_line
    registers = [0] * 8
    memory = [0] * 28
    special_registers = {'PC': 0, 'IR': '', 'MAR': 0, 'MDR': 0}
    instruction_history = []
    current_line = 0
    update_gui()

def on_verify():
    instructions = instruction_entry.get("1.0", tk.END).strip().split('\n')
    valid_ops = ['LOAD', 'STORE', 'MOVE', 'ADD', 'SUB', 'MUL', 'INC', 'DEC']
    for idx, instr in enumerate(instructions):
        if not instr.strip():
            continue
        try:
            tokens = instr.strip().split()
            op = tokens[0].upper()
            if op not in valid_ops:
                raise ValueError(f"Line {idx+1}: Invalid operation '{op}'")

            operands = []
            if len(tokens) > 1:
                operands = [operand.strip() for operand in ' '.join(tokens[1:]).split(',')]

            if op in ['LOAD', 'STORE']:
                if len(operands) != 2:
                    raise ValueError(f"Line {idx+1}: '{op}' needs 2 operands")
                if not operands[0].startswith('R'):
                    raise ValueError(f"Line {idx+1}: First operand must be a register")
            elif op in ['MOVE', 'ADD', 'SUB', 'MUL']:
                if len(operands) not in [2,3]:
                    raise ValueError(f"Line {idx+1}: '{op}' needs 2 or 3 operands")
                if len(operands) == 2:
                    if not all(o.startswith('R') for o in operands):
                        raise ValueError(f"Line {idx+1}: Both operands must be registers")
                else:  # 3 operands
                    if not all(o.startswith('R') for o in operands):
                        raise ValueError(f"Line {idx+1}: All operands must be registers")
            elif op in ['INC', 'DEC']:
                if len(operands) != 1:
                    raise ValueError(f"Line {idx+1}: '{op}' needs 1 operand")
                if not operands[0].startswith('R'):
                    raise ValueError(f"Line {idx+1}: Operand must be a register")
        except Exception as e:
            messagebox.showerror("Verification Error", str(e))
            return
    messagebox.showinfo("Verification", "All instructions are valid!")

# === GUI Layout ===
root = tk.Tk()
root.title("Instruction Set Simulator")
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)

# === Top row: Instruction Input and Registers ===
top_frame = tk.Frame(root, pady=5)
top_frame.grid(row=0, column=0, sticky="nsew")
root.rowconfigure(0, weight=0)
root.columnconfigure(0, weight=1)
top_frame.columnconfigure(0, weight=3)
top_frame.columnconfigure(1, weight=1)

instruction_box = tk.LabelFrame(top_frame, text="Instruction Input (Multiline Supported)", padx=5, pady=5)
instruction_box.grid(row=0, column=0, sticky="nsew", padx=5)
instruction_box.columnconfigure(0, weight=1)
instruction_entry = tk.Text(instruction_box, height=5, wrap="word", font=("Consolas", 14))
instruction_entry.grid(row=0, column=0, sticky="nsew")
instruction_box.grid_rowconfigure(0, weight=1)
instruction_box.grid_columnconfigure(0, weight=1)

register_box = tk.LabelFrame(top_frame, text="Registers", padx=5, pady=5)
register_box.grid(row=0, column=1, sticky="nsew", padx=5)
register_box.grid_rowconfigure(tuple(range(8)), weight=1)
register_box.grid_columnconfigure(1, weight=1)
register_box.columnconfigure(0, weight=1)
register_labels = []
for i in range(8):
    tk.Label(register_box, text=f"R{i}", width=3, anchor='e').grid(row=i, column=0, sticky="nsew")
    lbl = tk.Label(register_box, text="0", width=5, relief="sunken", anchor='w')
    lbl.grid(row=i, column=1, sticky="nsew")
    register_labels.append(lbl)

# === Middle row: Memory ===
memory_box = tk.LabelFrame(root, text="Memory", padx=5, pady=5)
memory_box.grid(row=1, column=0, sticky="nsew", pady=5)
root.rowconfigure(1, weight=1)
memory_box.columnconfigure(tuple(range(7)), weight=1)
memory_labels = []
for i in range(8):
    for j in range(8):
        idx = i * 8 + j
        lbl = tk.Label(memory_box, text="0", width=4, relief="sunken", anchor='w')
        lbl.grid(row=i, column=j, padx=2, pady=2, sticky="nsew")
        memory_box.grid_rowconfigure(i, weight=1)
        memory_box.grid_columnconfigure(j, weight=1)
        memory_labels.append(lbl)

# === Bus View ===
bus_box = tk.LabelFrame(root, text="System Buses", padx=5, pady=5)
bus_box.grid(row=1, column=1, sticky="nsew", pady=5, padx=5)
root.columnconfigure(1, weight=1)

bus_labels = {
    'Address Bus': tk.Label(bus_box, text="Address Bus: MAR", font=("Courier", 10), relief="sunken", anchor='w'),
    'Data Bus': tk.Label(bus_box, text="Data Bus: MDR", font=("Courier", 10), relief="sunken", anchor='w'),
    'Control Bus': tk.Label(bus_box, text="Control Bus: PC/IR", font=("Courier", 10), relief="sunken", anchor='w')
}

for idx, label in enumerate(bus_labels.values()):
    label.grid(row=idx, column=0, sticky="ew", padx=5, pady=2)
    bus_box.grid_rowconfigure(idx, weight=1)

# === Bottom row: Control Signals and Special Registers ===
bottom_frame = tk.Frame(root, pady=5)
bottom_frame.grid(row=2, column=0, sticky="nsew")
root.rowconfigure(2, weight=0)
bottom_frame.columnconfigure(0, weight=1)
bottom_frame.columnconfigure(1, weight=1)

control_box = tk.LabelFrame(bottom_frame, text="Control Signals", padx=5, pady=5)
control_box.grid(row=0, column=0, sticky="nsew", padx=5)
control_box.columnconfigure(tuple(range(4)), weight=1)
control_labels = []

special_box = tk.LabelFrame(bottom_frame, text="Special Registers", padx=5, pady=5)
special_box.grid(row=0, column=1, sticky="nsew", padx=5)
special_box.columnconfigure(1, weight=1)
special_labels = {}
for idx, key in enumerate(['PC', 'IR', 'MAR', 'MDR']):
    tk.Label(special_box, text=key, width=5, anchor='e').grid(row=idx, column=0, sticky="e")
    lbl = tk.Label(special_box, text="0", width=15, relief="sunken", anchor='w')
    lbl.grid(row=idx, column=1, sticky="ew")
    special_box.grid_rowconfigure(idx, weight=1)
    special_labels[key] = lbl
special_box.grid_columnconfigure(1, weight=1)
# Add FLAGS special register display
tk.Label(special_box, text='FLAGS', width=5, anchor='e').grid(row=4, column=0, sticky="e")
lbl = tk.Label(special_box, text="Z:0 N:0 C:0 V:0", width=15, relief="sunken", anchor='w')
lbl.grid(row=4, column=1, sticky="ew")
special_box.grid_rowconfigure(4, weight=1)
special_labels['FLAGS'] = lbl

# === Bottom buttons ===
button_frame = tk.Frame(root, pady=10)
button_frame.grid(row=3, column=0, sticky="ew")
root.rowconfigure(3, weight=0)
button_frame.columnconfigure(0, weight=1)
button_frame.columnconfigure(1, weight=1)
button_frame.columnconfigure(2, weight=1)
button_frame.columnconfigure(3, weight=1)
tk.Button(button_frame, text="Verify", command=on_verify, width=10).grid(row=0, column=0, padx=5, sticky="ew")
tk.Button(button_frame, text="Step", command=on_step, width=10).grid(row=0, column=1, padx=5, sticky="ew")
tk.Button(button_frame, text="Reset", command=on_reset, width=10).grid(row=0, column=2, padx=5, sticky="ew")
tk.Button(button_frame, text="Next", command=on_next, width=10).grid(row=0, column=3, padx=5, sticky="ew")

# === Start GUI ===
update_gui()
root.mainloop()


# to run :  python /Users/ayushjainayush/Downloads/ISS/issgui.py