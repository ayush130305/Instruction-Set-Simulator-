import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import json
import time

# === CPU STATE ===
class CPUState:
    def __init__(self):
        self.registers = [0] * 8
        self.memory = [0] * 64
        self.special_registers = {
            'PC': 0,
            'IR': '',
            'MAR': 0,
            'MDR': 0,
            'FLAGS': {'Z': 0, 'N': 0, 'C': 0, 'V': 0}
        }
        self.instruction_history = []
        self.current_line = 0
        self.modified_registers = set()
        self.modified_memory = set()
        self.animation_active = False
        
    def copy(self):
        state = CPUState()
        state.registers = self.registers.copy()
        state.memory = self.memory.copy()
        state.special_registers = {
            'PC': self.special_registers['PC'],
            'IR': self.special_registers['IR'],
            'MAR': self.special_registers['MAR'],
            'MDR': self.special_registers['MDR'],
            'FLAGS': self.special_registers['FLAGS'].copy()
        }
        state.instruction_history = self.instruction_history.copy()
        state.current_line = self.current_line
        return state
    
    def update_flags(self, result, original_result=None):
        """Update FLAGS based on operation result"""
        # Z flag: set if result is zero
        self.special_registers['FLAGS']['Z'] = 1 if result == 0 else 0
        
        # N flag: set if result is negative (bit 7 set in 8-bit)
        self.special_registers['FLAGS']['N'] = 1 if result & 0x80 else 0
        
        # C flag: set if carry occurred (result > 255 or < 0)
        if original_result is not None:
            self.special_registers['FLAGS']['C'] = 1 if original_result > 255 or original_result < 0 else 0
        
        # V flag: overflow (simplified - would need more context for proper implementation)
        # For now, set if result wrapped around
        if original_result is not None:
            self.special_registers['FLAGS']['V'] = 1 if original_result != result else 0

cpu_state = CPUState()
state_history = []  # For undo/redo
redo_stack = []
dark_mode = False
execution_speed = 500  # milliseconds

# === Instruction Execution Engine ===
def execute_instruction(instruction, line_num=None):
    try:
        cpu_state.modified_registers.clear()
        cpu_state.modified_memory.clear()
        
        # Remove comments from instruction
        if ';' in instruction:
            instruction = instruction[:instruction.index(';')]
        if '#' in instruction:
            instruction = instruction[:instruction.index('#')]
        
        tokens = instruction.strip().split()
        if len(tokens) < 1:
            return True

        op = tokens[0].upper()
        operands = []
        if len(tokens) > 1:
            # Join the rest and split by comma, preserving spaces within operands
            operands = [operand.strip() for operand in ' '.join(tokens[1:]).split(',')]

        # Bounds checking helper
        def check_register(reg_str):
            if not reg_str.startswith('R') or not reg_str[1:].isdigit():
                raise ValueError(f"Invalid register: {reg_str}")
            reg = int(reg_str[1:])
            if reg < 0 or reg > 7:
                raise ValueError(f"Register {reg_str} out of bounds (0-7)")
            return reg
        
        def check_memory(addr):
            if addr < 0 or addr >= 64:
                raise ValueError(f"Memory address {addr} out of bounds (0-63)")
            return addr

        if op == 'LOAD':
            if len(operands) != 2:
                raise ValueError(f"'{op}' requires 2 operands")
            reg = check_register(operands[0])
            value = int(operands[1], 0)
            cpu_state.special_registers['MAR'] = cpu_state.special_registers['PC']
            cpu_state.special_registers['MDR'] = value
            cpu_state.registers[reg] = value % 256
            cpu_state.modified_registers.add(reg)
            cpu_state.update_flags(cpu_state.registers[reg])

        elif op == 'STORE':
            if len(operands) != 2:
                raise ValueError(f"'{op}' requires 2 operands")
            reg = check_register(operands[0])
            address = check_memory(int(operands[1]))
            value = cpu_state.registers[reg] % 256
            cpu_state.memory[address] = value
            cpu_state.special_registers['MAR'] = address
            cpu_state.special_registers['MDR'] = value
            cpu_state.modified_memory.add(address)

        elif op == 'MOV':
            if len(operands) != 2:
                raise ValueError(f"'{op}' requires 2 operands")
            reg = check_register(operands[0])
            src = check_register(operands[1])
            cpu_state.registers[reg] = cpu_state.registers[src] % 256
            cpu_state.modified_registers.add(reg)
            cpu_state.update_flags(cpu_state.registers[reg])

        elif op in ['ADD', 'SUB', 'MUL']:
            if len(operands) == 2:
                reg = check_register(operands[0])
                src = check_register(operands[1])
                if op == 'ADD':
                    original = cpu_state.registers[reg] + cpu_state.registers[src]
                    cpu_state.registers[reg] = original % 256
                elif op == 'SUB':
                    original = cpu_state.registers[reg] - cpu_state.registers[src]
                    cpu_state.registers[reg] = original % 256
                elif op == 'MUL':
                    original = cpu_state.registers[reg] * cpu_state.registers[src]
                    cpu_state.registers[reg] = original % 256
                cpu_state.modified_registers.add(reg)
                cpu_state.update_flags(cpu_state.registers[reg], original)
            elif len(operands) == 3:
                dest = check_register(operands[0])
                src1 = check_register(operands[1])
                src2 = check_register(operands[2])
                if op == 'ADD':
                    original = cpu_state.registers[src1] + cpu_state.registers[src2]
                elif op == 'SUB':
                    original = cpu_state.registers[src1] - cpu_state.registers[src2]
                elif op == 'MUL':
                    original = cpu_state.registers[src1] * cpu_state.registers[src2]
                cpu_state.registers[dest] = original % 256
                cpu_state.modified_registers.add(dest)
                cpu_state.update_flags(cpu_state.registers[dest], original)
            else:
                raise ValueError(f"'{op}' requires 2 or 3 operands")

        elif op == 'INC':
            if len(operands) != 1:
                raise ValueError(f"'{op}' requires 1 operand")
            reg = check_register(operands[0])
            original = cpu_state.registers[reg] + 1
            cpu_state.registers[reg] = original % 256
            cpu_state.modified_registers.add(reg)
            cpu_state.update_flags(cpu_state.registers[reg], original)

        elif op == 'DEC':
            if len(operands) != 1:
                raise ValueError(f"'{op}' requires 1 operand")
            reg = check_register(operands[0])
            original = cpu_state.registers[reg] - 1
            cpu_state.registers[reg] = original % 256
            cpu_state.modified_registers.add(reg)
            cpu_state.update_flags(cpu_state.registers[reg], original)

        elif op == 'CMP':
            if len(operands) != 2:
                raise ValueError(f"'{op}' requires 2 operands")
            reg1 = check_register(operands[0])
            reg2 = check_register(operands[1])
            result = cpu_state.registers[reg1] - cpu_state.registers[reg2]
            cpu_state.update_flags(result % 256, result)

        elif op == 'JMP':
            if len(operands) != 1:
                raise ValueError(f"'{op}' requires 1 operand")
            target = int(operands[0])
            cpu_state.special_registers['PC'] = target
            cpu_state.current_line = target
            cpu_state.special_registers['IR'] = instruction
            return True

        elif op == 'JZ':
            if len(operands) != 1:
                raise ValueError(f"'{op}' requires 1 operand")
            if cpu_state.special_registers['FLAGS']['Z'] == 1:
                target = int(operands[0])
                cpu_state.special_registers['PC'] = target
                cpu_state.current_line = target
                cpu_state.special_registers['IR'] = instruction
                return True

        elif op == 'JNZ':
            if len(operands) != 1:
                raise ValueError(f"'{op}' requires 1 operand")
            if cpu_state.special_registers['FLAGS']['Z'] == 0:
                target = int(operands[0])
                cpu_state.special_registers['PC'] = target
                cpu_state.current_line = target
                cpu_state.special_registers['IR'] = instruction
                return True

        elif op == 'JC':
            if len(operands) != 1:
                raise ValueError(f"'{op}' requires 1 operand")
            if cpu_state.special_registers['FLAGS']['C'] == 1:
                target = int(operands[0])
                cpu_state.special_registers['PC'] = target
                cpu_state.current_line = target
                cpu_state.special_registers['IR'] = instruction
                return True

        elif op == 'JN':
            if len(operands) != 1:
                raise ValueError(f"'{op}' requires 1 operand")
            if cpu_state.special_registers['FLAGS']['N'] == 1:
                target = int(operands[0])
                cpu_state.special_registers['PC'] = target
                cpu_state.current_line = target
                cpu_state.special_registers['IR'] = instruction
                return True

        elif op == 'NOP':
            pass

        elif op.startswith(';') or op.startswith('#'):
            # Comment - skip
            pass

        else:
            raise ValueError(f"Unknown instruction: {op}")

        cpu_state.special_registers['IR'] = instruction
        cpu_state.special_registers['PC'] += 1
        return True

    except Exception as e:
        if line_num is not None:
            messagebox.showerror("Execution Error", f"Line {line_num + 1}: {str(e)}")
        else:
            messagebox.showerror("Execution Error", str(e))
        return False

# === GUI Update Functions ===
def update_gui():
    # Update registers with highlighting
    for i in range(8):
        value = cpu_state.registers[i]
        register_labels[i]["text"] = str(value)
        if i in cpu_state.modified_registers:
            register_labels[i]["bg"] = "#ffeb3b" if not dark_mode else "#ffc107"
            root.after(300, lambda lbl=register_labels[i]: lbl.config(bg=get_bg_color()))
        else:
            register_labels[i]["bg"] = get_bg_color()
    
    # Update memory with highlighting
    for i in range(len(cpu_state.memory)):
        value = cpu_state.memory[i]
        memory_labels[i]["text"] = str(value)
        if i in cpu_state.modified_memory:
            memory_labels[i]["bg"] = "#ffeb3b" if not dark_mode else "#ffc107"
            root.after(300, lambda lbl=memory_labels[i]: lbl.config(bg=get_bg_color()))
        else:
            memory_labels[i]["bg"] = get_bg_color()
    
    # Update special registers
    for k in cpu_state.special_registers:
        if k == 'FLAGS':
            continue
        special_labels[k]["text"] = str(cpu_state.special_registers[k])
    
    # Update FLAGS
    flags_text = ' '.join(f"{k}:{v}" for k, v in cpu_state.special_registers['FLAGS'].items())
    special_labels['FLAGS']["text"] = flags_text
    
    # Update control signals
    for widget in control_box.winfo_children():
        widget.destroy()
    
    max_labels = 8
    display_history = cpu_state.instruction_history[-max_labels:]
    for idx, instr in enumerate(display_history):
        row = idx // 4
        col = idx % 4
        lbl = tk.Label(control_box, text=instr, width=10, relief="sunken", anchor='w',
                      bg=get_bg_color(), fg=get_fg_color())
        lbl.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
    
    # Update buses
    bus_labels['Address Bus']["text"] = f"Address Bus: {cpu_state.special_registers.get('MAR', '')}"
    bus_labels['Data Bus']["text"] = f"Data Bus: {cpu_state.special_registers.get('MDR', '')}"
    bus_labels['Control Bus']["text"] = f"Control Bus: PC={cpu_state.special_registers.get('PC', '')} IR={cpu_state.special_registers.get('IR', '')}"
    
    # Highlight current line
    highlight_current_line()
    
    # Animate data flow
    if cpu_state.animation_active:
        animate_data_flow()

def highlight_current_line():
    instruction_entry.tag_remove("current_line", "1.0", tk.END)
    if cpu_state.current_line > 0:
        line_start = f"{cpu_state.current_line}.0"
        line_end = f"{cpu_state.current_line}.end"
        instruction_entry.tag_add("current_line", line_start, line_end)
        instruction_entry.tag_config("current_line", background="#90caf9" if not dark_mode else "#1976d2")

def animate_data_flow():
    """Simple animation effect for data flow"""
    # This creates a brief visual pulse
    for lbl in bus_labels.values():
        original_bg = lbl["bg"]
        lbl["bg"] = "#4caf50"
        root.after(200, lambda l=lbl, bg=original_bg: l.config(bg=bg))

def save_state():
    """Save current state for undo"""
    state_history.append(cpu_state.copy())
    if len(state_history) > 50:  # Limit history
        state_history.pop(0)
    redo_stack.clear()

def on_step():
    save_state()
    instructions = instruction_entry.get("1.0", tk.END).strip().split('\n')
    for i, instruction in enumerate(instructions):
        if instruction.strip() and not instruction.strip().startswith(';') and not instruction.strip().startswith('#'):
            cpu_state.instruction_history.append(instruction.strip())
            cpu_state.animation_active = True
            execute_instruction(instruction, i)
    update_gui()

def on_next():
    save_state()
    instructions = instruction_entry.get("1.0", tk.END).strip().split('\n')
    max_iterations = 1000  # Prevent infinite loops
    iterations = 0
    
    while cpu_state.current_line < len(instructions) and iterations < max_iterations:
        instruction = instructions[cpu_state.current_line].strip()
        if instruction and not instruction.startswith(';') and not instruction.startswith('#'):
            cpu_state.instruction_history.append(instruction)
            cpu_state.animation_active = True
            if not execute_instruction(instruction, cpu_state.current_line):
                break
            update_gui()
            root.update()
            time.sleep(execution_speed / 1000.0)
            
            # Check if PC was modified by jump
            if cpu_state.current_line != cpu_state.special_registers['PC']:
                cpu_state.current_line = cpu_state.special_registers['PC']
                continue
        
        cpu_state.current_line += 1
        iterations += 1
    
    if iterations >= max_iterations:
        messagebox.showwarning("Execution Stopped", "Maximum iterations reached. Possible infinite loop.")

def on_reset():
    global cpu_state
    save_state()
    cpu_state = CPUState()
    update_gui()

def on_undo():
    global cpu_state
    if state_history:
        redo_stack.append(cpu_state.copy())
        cpu_state = state_history.pop()
        update_gui()

def on_redo():
    global cpu_state
    if redo_stack:
        state_history.append(cpu_state.copy())
        cpu_state = redo_stack.pop()
        update_gui()

def on_verify():
    instructions = instruction_entry.get("1.0", tk.END).strip().split('\n')
    valid_ops = ['LOAD', 'STORE', 'MOV', 'ADD', 'SUB', 'MUL', 'INC', 'DEC', 'CMP', 'JMP', 'JZ', 'JNZ', 'JC', 'JN', 'NOP']
    errors = []
    
    for idx, instr in enumerate(instructions):
        if not instr.strip() or instr.strip().startswith(';') or instr.strip().startswith('#'):
            continue
        try:
            tokens = instr.strip().split()
            op = tokens[0].upper()
            if op not in valid_ops:
                errors.append(f"Line {idx+1}: Invalid operation '{op}'")
                continue

            operands = []
            if len(tokens) > 1:
                operands = [operand.strip() for operand in ' '.join(tokens[1:]).split(',')]

            if op in ['LOAD', 'STORE', 'CMP', 'MOV']:
                if len(operands) != 2:
                    errors.append(f"Line {idx+1}: '{op}' needs 2 operands")
            elif op in ['ADD', 'SUB', 'MUL']:
                if len(operands) not in [2, 3]:
                    errors.append(f"Line {idx+1}: '{op}' needs 2 or 3 operands")
            elif op in ['INC', 'DEC', 'JMP', 'JZ', 'JNZ', 'JC', 'JN']:
                if len(operands) != 1:
                    errors.append(f"Line {idx+1}: '{op}' needs 1 operand")
        except Exception as e:
            errors.append(f"Line {idx+1}: {str(e)}")
    
    if errors:
        messagebox.showerror("Verification Errors", "\n".join(errors))
    else:
        messagebox.showinfo("Verification", "All instructions are valid!")

def save_program():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".asm",
        filetypes=[("Assembly files", "*.asm"), ("Text files", "*.txt"), ("All files", "*.*")]
    )
    if file_path:
        with open(file_path, 'w') as f:
            f.write(instruction_entry.get("1.0", tk.END))
        messagebox.showinfo("Save", "Program saved successfully!")

def load_program():
    file_path = filedialog.askopenfilename(
        filetypes=[("Assembly files", "*.asm"), ("Text files", "*.txt"), ("All files", "*.*")]
    )
    if file_path:
        with open(file_path, 'r') as f:
            content = f.read()
        instruction_entry.delete("1.0", tk.END)
        instruction_entry.insert("1.0", content)
        apply_syntax_highlighting()

def apply_syntax_highlighting():
    """Apply syntax highlighting to instruction text"""
    instruction_entry.tag_remove("keyword", "1.0", tk.END)
    instruction_entry.tag_remove("register", "1.0", tk.END)
    instruction_entry.tag_remove("number", "1.0", tk.END)
    instruction_entry.tag_remove("comment", "1.0", tk.END)
    instruction_entry.tag_remove("address", "1.0", tk.END)
    
    keywords = ['LOAD', 'STORE', 'MOV', 'ADD', 'SUB', 'MUL', 'INC', 'DEC', 'CMP', 'JMP', 'JZ', 'JNZ', 'JC', 'JN', 'NOP']
    
    content = instruction_entry.get("1.0", tk.END)
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Highlight comments
        if ';' in line or '#' in line:
            comment_start = line.find(';') if ';' in line else line.find('#')
            start_idx = f"{line_num}.{comment_start}"
            end_idx = f"{line_num}.end"
            instruction_entry.tag_add("comment", start_idx, end_idx)
        
        # Highlight keywords
        for keyword in keywords:
            if keyword.lower() in line.lower() or keyword in line:
                start = 0
                while True:
                    start = line.upper().find(keyword, start)
                    if start == -1:
                        break
                    end = start + len(keyword)
                    start_idx = f"{line_num}.{start}"
                    end_idx = f"{line_num}.{end}"
                    instruction_entry.tag_add("keyword", start_idx, end_idx)
                    start = end
        
        # Highlight registers
        import re
        for match in re.finditer(r'\bR[0-7]\b', line):
            start_idx = f"{line_num}.{match.start()}"
            end_idx = f"{line_num}.{match.end()}"
            instruction_entry.tag_add("register", start_idx, end_idx)
        
        # Highlight memory addresses (RxC format)
        for match in re.finditer(r'\b[0-7]x[0-7]\b', line):
            start_idx = f"{line_num}.{match.start()}"
            end_idx = f"{line_num}.{match.end()}"
            instruction_entry.tag_add("address", start_idx, end_idx)
        
        # Highlight numbers
        for match in re.finditer(r'\b\d+\b', line):
            start_idx = f"{line_num}.{match.start()}"
            end_idx = f"{line_num}.{match.end()}"
            instruction_entry.tag_add("number", start_idx, end_idx)
    
    # Configure tag colors
    if dark_mode:
        instruction_entry.tag_config("keyword", foreground="#bb86fc")
        instruction_entry.tag_config("register", foreground="#03dac6")
        instruction_entry.tag_config("number", foreground="#ffa726")
        instruction_entry.tag_config("address", foreground="#4fc3f7")
        instruction_entry.tag_config("comment", foreground="#666666")
    else:
        instruction_entry.tag_config("keyword", foreground="#0000ff")
        instruction_entry.tag_config("register", foreground="#008000")
        instruction_entry.tag_config("number", foreground="#ff6600")
        instruction_entry.tag_config("address", foreground="#1976d2")
        instruction_entry.tag_config("comment", foreground="#999999")

def toggle_dark_mode():
    global dark_mode
    dark_mode = not dark_mode
    apply_theme()
    # Update button text
    dark_mode_btn.config(text="🌙 Dark Mode" if not dark_mode else "☀️ Light Mode")

def get_bg_color():
    return "#1e1e1e" if dark_mode else "#ffffff"

def get_fg_color():
    return "#ffffff" if dark_mode else "#000000"

def apply_theme():
    bg = get_bg_color()
    fg = get_fg_color()
    frame_bg = "#2d2d2d" if dark_mode else "#f0f0f0"
    
    root.config(bg=bg)
    
    # Update all frames
    for frame in [top_frame, bottom_frame, button_frame]:
        frame.config(bg=bg)
    
    # Update text widget
    instruction_entry.config(bg=bg, fg=fg, insertbackground=fg)
    
    # Update all labels
    for lbl in register_labels + memory_labels + list(special_labels.values()) + list(bus_labels.values()):
        lbl.config(bg=frame_bg if dark_mode else "#ffffff", fg=fg)
    
    # Update label frames
    for frame in [instruction_box, register_box, memory_box, bus_box, control_box, special_box]:
        frame.config(bg=bg, fg=fg)
    
    # Update dark mode button
    dark_mode_btn.config(
        bg="#424242" if dark_mode else "#e0e0e0",
        fg=fg,
        activebackground="#616161" if dark_mode else "#d0d0d0"
    )
    
    apply_syntax_highlighting()
    update_gui()

def change_speed():
    global execution_speed
    speed_window = tk.Toplevel(root)
    speed_window.title("Execution Speed")
    speed_window.geometry("300x150")
    
    tk.Label(speed_window, text="Execution Speed (ms):").pack(pady=10)
    
    speed_var = tk.IntVar(value=execution_speed)
    scale = tk.Scale(speed_window, from_=100, to=2000, orient=tk.HORIZONTAL, 
                    variable=speed_var, length=200)
    scale.pack(pady=10)
    
    def apply_speed():
        global execution_speed
        execution_speed = speed_var.get()
        speed_window.destroy()
    
    tk.Button(speed_window, text="Apply", command=apply_speed).pack(pady=10)

def show_help():
    """Display help window with all instruction syntax"""
    help_window = tk.Toplevel(root)
    help_window.title("Help - Instruction Syntax")
    help_window.geometry("700x600")
    
    # Create a text widget with scrollbar
    help_frame = tk.Frame(help_window)
    help_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    help_text = tk.Text(help_frame, wrap=tk.WORD, font=("Courier", 10), height=30, width=80)
    scrollbar = tk.Scrollbar(help_frame, command=help_text.yview)
    help_text.config(yscrollcommand=scrollbar.set)
    
    help_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Help content
    help_content = """
================================================================================
                    INSTRUCTION SET SIMULATOR - HELP GUIDE
================================================================================

SUPPORTED INSTRUCTIONS AND SYNTAX:

1. LOAD (Load Immediate Value)
   Syntax: LOAD <register>, <value>
   Example: LOAD R0, 10
   Description: Loads an immediate value into a register
   Registers: R0-R7
   Value: 0-255 (8-bit)

2. STORE (Store Register to Memory)
   Syntax: STORE <register>, <address>
   Example: STORE R0, 10
   Description: Stores the value from a register to memory
   Registers: R0-R7
   Address: 0-63 (Memory location as decimal)
   Format: Can also use RxC notation (Row x Column, e.g., 2x5)

3. MOV (Move Register to Register)
   Syntax: MOV <destination>, <source>
   Example: MOV R1, R0
   Description: Copies value from source register to destination
   Registers: R0-R7 for both operands

4. ADD (Addition)
   Syntax: ADD <register>, <register>
          ADD <destination>, <source1>, <source2>
   Example: ADD R0, R1  or  ADD R2, R0, R1
   Description: Adds two register values
   2-operand form: Adds R1 to R0, stores in R0
   3-operand form: Adds R0+R1, stores in R2

5. SUB (Subtraction)
   Syntax: SUB <register>, <register>
          SUB <destination>, <source1>, <source2>
   Example: SUB R0, R1  or  SUB R2, R0, R1
   Description: Subtracts register values
   2-operand form: R0 = R0 - R1
   3-operand form: R2 = R0 - R1

6. MUL (Multiplication)
   Syntax: MUL <register>, <register>
          MUL <destination>, <source1>, <source2>
   Example: MUL R0, R1  or  MUL R2, R0, R1
   Description: Multiplies register values
   2-operand form: R0 = R0 * R1
   3-operand form: R2 = R0 * R1

7. INC (Increment)
   Syntax: INC <register>
   Example: INC R0
   Description: Increments register by 1
   Registers: R0-R7

8. DEC (Decrement)
   Syntax: DEC <register>
   Example: DEC R0
   Description: Decrements register by 1
   Registers: R0-R7

9. CMP (Compare)
   Syntax: CMP <register>, <register>
   Example: CMP R0, R1
   Description: Compares two registers and sets FLAGS
   Sets Z flag if equal, N flag if negative, etc.

10. JMP (Jump Unconditional)
    Syntax: JMP <line_number>
    Example: JMP 5
    Description: Unconditionally jumps to specified line
    Line: 0-based line number

11. JZ (Jump if Zero)
    Syntax: JZ <line_number>
    Example: JZ 10
    Description: Jumps to line if Z flag is set (result was zero)
    Line: 0-based line number

12. JNZ (Jump if Not Zero)
    Syntax: JNZ <line_number>
    Example: JNZ 8
    Description: Jumps to line if Z flag is clear (result was not zero)
    Line: 0-based line number

13. JC (Jump if Carry)
    Syntax: JC <line_number>
    Example: JC 12
    Description: Jumps to line if C flag is set (carry occurred)
    Line: 0-based line number

14. JN (Jump if Negative)
    Syntax: JN <line_number>
    Example: JN 6
    Description: Jumps to line if N flag is set (result was negative)
    Line: 0-based line number

15. NOP (No Operation)
    Syntax: NOP
    Example: NOP
    Description: Does nothing, just increments PC

================================================================================
COMMENTS:
   Use semicolon (;) or hash (#) for comments
   Example: LOAD R0, 10  ; Load 10 into R0
           LOAD R1, 20  # Load 20 into R1

FLAGS REGISTER:
   Z (Zero): Set if result equals zero
   N (Negative): Set if bit 7 is set (result > 127)
   C (Carry): Set if overflow occurred
   V (Overflow): Set if result wrapped

REGISTERS:
   R0-R7: 8 General Purpose Registers (8-bit each)

MEMORY:
   64 bytes total (0-63)
   Can be addressed as decimal (0-63) or matrix (RxC format)
   Memory display: 8x8 Matrix with headers

SPECIAL REGISTERS:
   PC (Program Counter): Current instruction line
   IR (Instruction Register): Current instruction
   MAR (Memory Address Register): Current memory address
   MDR (Memory Data Register): Current memory data
   FLAGS: Condition flags (Z, N, C, V)

BUTTONS:
   Verify: Check syntax of all instructions
   Step All: Execute all instructions once
   Next: Execute instructions with animation
   Reset: Clear all registers and memory
   Undo: Revert to previous state
   Redo: Restore next state
   Load: Load a program from file
   Save: Save current program to file

================================================================================
    """
    
    help_text.insert("1.0", help_content)
    help_text.config(state=tk.DISABLED)  # Make read-only
    
    # Close button
    close_btn = tk.Button(help_window, text="Close", command=help_window.destroy, width=15)
    close_btn.pack(pady=10)

# === GUI Layout ===
root = tk.Tk()
root.title("Enhanced Instruction Set Simulator")
root.geometry("1400x900")

# Configure root grid to be responsive
root.grid_rowconfigure(0, weight=1)  # Top section with instructions and registers
root.grid_rowconfigure(1, weight=2)  # Memory and buses section
root.grid_rowconfigure(2, weight=1)  # Special registers and control
root.grid_rowconfigure(3, weight=0)  # Buttons (fixed)
root.grid_columnconfigure(0, weight=2)  # Left column (wider)
root.grid_columnconfigure(1, weight=1)  # Right column

# Menu bar
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Load Program", command=load_program)
file_menu.add_command(label="Save Program", command=save_program)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

edit_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Edit", menu=edit_menu)
edit_menu.add_command(label="Undo", command=on_undo, accelerator="Ctrl+Z")
edit_menu.add_command(label="Redo", command=on_redo, accelerator="Ctrl+Y")

view_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="View", menu=view_menu)
view_menu.add_command(label="Toggle Dark Mode", command=toggle_dark_mode)
view_menu.add_command(label="Change Speed", command=change_speed)

help_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(label="Show Help", command=show_help)

# Top row: Instruction Input and Registers
top_frame = tk.Frame(root)
top_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
top_frame.grid_rowconfigure(0, weight=1)
top_frame.grid_columnconfigure(0, weight=3)  # Instruction box gets more space
top_frame.grid_columnconfigure(1, weight=1)  # Register box

instruction_box = tk.LabelFrame(top_frame, text="Instruction Input", padx=5, pady=5)
instruction_box.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
instruction_box.grid_rowconfigure(0, weight=1)
instruction_box.grid_columnconfigure(0, weight=1)

instruction_entry = tk.Text(instruction_box, height=8, wrap="word", font=("Consolas", 11))
instruction_entry.grid(row=0, column=0, sticky="nsew")
instruction_entry.bind("<KeyRelease>", lambda e: apply_syntax_highlighting())

# Add scrollbar
scrollbar = tk.Scrollbar(instruction_box, command=instruction_entry.yview)
scrollbar.grid(row=0, column=1, sticky="ns")
instruction_entry.config(yscrollcommand=scrollbar.set)

register_box = tk.LabelFrame(top_frame, text="Registers", padx=5, pady=5)
register_box.grid(row=0, column=1, sticky="nsew")
register_box.grid_columnconfigure(0, weight=1)
register_box.grid_columnconfigure(1, weight=1)

register_labels = []
for i in range(8):
    register_box.grid_rowconfigure(i, weight=1)
    tk.Label(register_box, text=f"R{i}", width=3, anchor='e').grid(row=i, column=0, sticky="e", padx=2, pady=2)
    lbl = tk.Label(register_box, text="0", width=8, relief="sunken", anchor='w')
    lbl.grid(row=i, column=1, sticky="ew", padx=2, pady=2)
    register_labels.append(lbl)

# Middle row: Memory and Buses
memory_box = tk.LabelFrame(root, text="Memory (8x8 Matrix - Use RxC format: Row x Column)", padx=5, pady=5)
memory_box.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

# Add row and column headers
tk.Label(memory_box, text="", width=2).grid(row=0, column=0)
for j in range(8):
    lbl = tk.Label(memory_box, text=f"{j}", width=4, font=("Courier", 9, "bold"), fg="#666")
    lbl.grid(row=0, column=j+1, sticky="nsew")
    memory_box.grid_columnconfigure(j+1, weight=1)

memory_labels = []
for i in range(8):
    memory_box.grid_rowconfigure(i+1, weight=1)
    # Row header
    lbl = tk.Label(memory_box, text=f"{i}", width=2, font=("Courier", 9, "bold"), fg="#666")
    lbl.grid(row=i+1, column=0, sticky="nsew")
    
    for j in range(8):
        idx = i * 8 + j
        lbl = tk.Label(memory_box, text="0", width=4, relief="sunken", anchor='center')
        lbl.grid(row=i+1, column=j+1, padx=1, pady=1, sticky="nsew")
        memory_labels.append(lbl)

# Buses
bus_box = tk.LabelFrame(root, text="System Buses", padx=5, pady=5)
bus_box.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
bus_box.grid_rowconfigure(0, weight=1)
bus_box.grid_rowconfigure(1, weight=1)
bus_box.grid_rowconfigure(2, weight=1)
bus_box.grid_rowconfigure(3, weight=1)
bus_box.grid_columnconfigure(0, weight=1)

bus_labels = {}
for idx, bus_name in enumerate(['Address Bus', 'Data Bus', 'Control Bus']):
    lbl = tk.Label(bus_box, text=f"{bus_name}: ", font=("Courier", 10), 
                  relief="sunken", anchor='w', wraplength=300)
    lbl.grid(row=idx, column=0, sticky="nsew", padx=5, pady=5)
    bus_labels[bus_name] = lbl

# Dark mode toggle button in bus box
dark_mode_btn = tk.Button(bus_box, text="🌙 Dark Mode", command=toggle_dark_mode, width=15)
dark_mode_btn.grid(row=3, column=0, sticky="ew", padx=5, pady=5)

# Bottom row: Control Signals and Special Registers
bottom_frame = tk.Frame(root)
bottom_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
bottom_frame.grid_rowconfigure(0, weight=1)
bottom_frame.grid_columnconfigure(0, weight=2)
bottom_frame.grid_columnconfigure(1, weight=1)

control_box = tk.LabelFrame(bottom_frame, text="Control Signals", padx=5, pady=5)
control_box.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

for i in range(2):
    control_box.grid_rowconfigure(i, weight=1)
for j in range(4):
    control_box.grid_columnconfigure(j, weight=1)

special_box = tk.LabelFrame(bottom_frame, text="Special Registers", padx=5, pady=5)
special_box.grid(row=0, column=1, sticky="nsew")
special_box.grid_columnconfigure(0, weight=1)
special_box.grid_columnconfigure(1, weight=2)

special_labels = {}
for idx, key in enumerate(['PC', 'IR', 'MAR', 'MDR', 'FLAGS']):
    special_box.grid_rowconfigure(idx, weight=1)
    tk.Label(special_box, text=key, width=6, anchor='e').grid(row=idx, column=0, sticky="e", padx=2, pady=2)
    if key == 'FLAGS':
        lbl = tk.Label(special_box, text="Z:0 N:0 C:0 V:0", width=20, relief="sunken", anchor='w')
    else:
        lbl = tk.Label(special_box, text="0", width=20, relief="sunken", anchor='w')
    lbl.grid(row=idx, column=1, sticky="ew", padx=2, pady=2)
    special_labels[key] = lbl

# Buttons
button_frame = tk.Frame(root)
button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

buttons = [
    ("Verify", on_verify),
    ("Step All", on_step),
    ("Next", on_next),
    ("Reset", on_reset),
    ("Undo", on_undo),
    ("Redo", on_redo),
    ("Load", load_program),
    ("Save", save_program)
]

for idx, (text, command) in enumerate(buttons):
    button_frame.grid_columnconfigure(idx, weight=1)
    btn = tk.Button(button_frame, text=text, command=command, width=10, height=2)
    btn.grid(row=0, column=idx, padx=3, pady=3, sticky="ew")

# Keyboard shortcuts
root.bind("<Control-z>", lambda e: on_undo())
root.bind("<Control-y>", lambda e: on_redo())
root.bind("<Control-s>", lambda e: save_program())
root.bind("<Control-o>", lambda e: load_program())

# Load example program
example_program = """

LOAD R0,10       
STORE R0,10    
LOAD R1,20       
STORE R1,11    
LOAD R2,30      
STORE R2,22

LOAD R3,10       
LOAD R4,11      
ADD R5,R3,R4    
STORE R5,37   


LOAD R6,0       
LOAD R7,5         

INC R6           
CMP R6,R7       
JNZ 19             
STORE R6,10  
"""

instruction_entry.insert("1.0", example_program)
apply_syntax_highlighting()

# Initialize GUI
update_gui()
root.mainloop()
