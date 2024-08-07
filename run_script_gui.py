import tkinter as tk
import subprocess

def run_script():
    subprocess.call(['python', 'tcgplayerOrderImagesGet.py'])

root = tk.Tk()
root.title("Run Script")

run_button = tk.Button(root, text="Run Script", command=run_script, font=("Arial", 24))
run_button.pack(pady=20, padx=20)

root.mainloop()
