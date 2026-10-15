import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from scipy.io import loadmat

import database as db
from app_peep_trial import get_initial_peep, get_peep_sequence, get_next_peep

BG = "#F3F5F8"
TEXT = "#172033"
MUTED = "#64748B"
STEP_SECONDS = 120  # each PEEP step is maintained for 2 minutes

# ---------------------------------------------------------------
# DICTIONARIES + EIDORS 
# ---------------------------------------------------------------
project_folder = os.path.dirname(os.path.abspath(__file__))

constant_dictionary = {
    "voltage_meting": 0,
    "mesh": 0,
    "lowpass_cutoff": 0.6,
    "num_breaths_to_average": 3,
} # als dit central wordt opgeslagen, kunnen we het later aanpassen in de GUI 


def new_trial_dictionaries():
    trial_data_value = {
        "PEEP": [], "p_plateau": [], "indices": [], "compliance": [],
        "collapse": [], "overdistantion": [], "optimal_peep": 0,
    }
    trial_data_frames = {
        "Eidors_imgs": [], "Eidors_time": [], "inspiration_frame": [],
        "expiration_frame": [], "compliance_matrix": [], "collapse_matrix": [],
        "overdistantion_matrix": [],
    }
    return trial_data_value, trial_data_frames


def run_eidors(data_path):
    """Runs MATLAB/EIDORS on one EIT file and returns (imgs, time)."""
    subprocess.run(
        ["matlab", "-batch", f"cd('{project_folder}'); test_EIT('{data_path}')"],
        check=True,
    )
    data = loadmat(os.path.join(project_folder, "EIT_reconstructed.mat"))
    return data["imgs"], data["time"].flatten()


def to_float(text):
    return float(text.strip().replace(",", "."))  # accepts 12,5 and 12.5


def show_value(x):
    return "-" if x is None or x == "" else f"{x:g}" if isinstance(x, float) else str(x)


# ---------------------------------------------------------------
# THE APP: one window that swaps between screens
# ---------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Clinical Lung Monitoring")
        self.geometry("820x860")
        self.minsize(760, 760)
        self.configure(bg=BG)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("TLabelframe", background=BG)
        style.configure("TLabelframe.Label", background=BG, foreground=TEXT,
                        font=("Arial", 11, "bold"))

        # data shared by all screens
        self.doctor = ""
        self.trial_id = None
        self.baseline = {}
        self.sequence = []
        self.step_index = 0
        self.trial_data_value, self.trial_data_frames = new_trial_dictionaries()

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.screens = {}
        for S in (LoginScreen, WelcomeScreen, LibraryScreen, BaselineScreen,
                  RecommendationScreen, StepsScreen):
            screen = S(container, self)
            self.screens[S.__name__] = screen
            screen.grid(row=0, column=0, sticky="nsew")

        self.show("LoginScreen")

    def show(self, name):
        screen = self.screens[name]
        screen.on_show()      # lets the screen refresh itself
        screen.tkraise()      # bring it to the front

    def begin_trial(self, data):
        """Called when the baseline is valid: stores it and creates the trial in the database."""
        self.baseline = data
        self.sequence = get_peep_sequence(data["initial_peep"])
        self.step_index = 0
        self.trial_data_value, self.trial_data_frames = new_trial_dictionaries()
        self.trial_id = db.create_trial(self.doctor, data)


class Screen(ttk.Frame):
    """Base class for every screen."""

    def __init__(self, parent, app):
        super().__init__(parent, padding=24)
        self.app = app

    def heading(self, text, sub=""):
        ttk.Label(self, text=text, font=("Arial", 22, "bold")).pack(anchor="w")
        if sub:
            ttk.Label(self, text=sub, foreground=MUTED).pack(anchor="w", pady=(4, 16))

    def on_show(self):
        pass


# ---------------- 1. login ----------------
class LoginScreen(Screen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.user = tk.StringVar()
        self.pw = tk.StringVar()
        self.heading("Clinical Lung Monitoring", "Doctor login")

        form = ttk.Frame(self)
        form.pack(anchor="w")
        ttk.Label(form, text="Username").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Entry(form, textvariable=self.user, width=28).grid(row=0, column=1, padx=10)
        ttk.Label(form, text="Password").grid(row=1, column=0, sticky="w", pady=6)
        pw_entry = ttk.Entry(form, textvariable=self.pw, show="*", width=28)
        pw_entry.grid(row=1, column=1, padx=10)
        pw_entry.bind("<Return>", lambda e: self.login())  # Enter key = login

        buttons = ttk.Frame(self)
        buttons.pack(anchor="w", pady=14)
        ttk.Button(buttons, text="Log in", command=self.login).pack(side="left")
        ttk.Button(buttons, text="Create account", command=self.register).pack(side="left", padx=8)

    def on_show(self):
        self.pw.set("")

    def login(self):
        name = self.user.get().strip()
        if db.check_login(name, self.pw.get()):
            self.app.doctor = name
            self.app.show("WelcomeScreen")
        else:
            messagebox.showerror("Login failed", "Wrong username or password.")

    def register(self):
        name, pw = self.user.get().strip(), self.pw.get()
        if not name or len(pw) < 8:
            messagebox.showerror("Invalid", "Enter a username and a password of at least 8 characters.")
        elif db.create_user(name, pw):
            messagebox.showinfo("Account created", "You can now log in.")
        else:
            messagebox.showerror("Invalid", "That username already exists.")


# ---------------- 2. welcome ----------------
class WelcomeScreen(Screen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.heading("Welcome", "Search the library or start a new PEEP trial.")
        self.greeting = ttk.Label(self, text="", font=("Arial", 12))
        self.greeting.pack(anchor="w", pady=(0, 16))
        ttk.Button(self, text="Start new PEEP trial", width=30,
                   command=lambda: app.show("BaselineScreen")).pack(anchor="w", pady=6, ipady=8)
        ttk.Button(self, text="Search library", width=30,
                   command=lambda: app.show("LibraryScreen")).pack(anchor="w", pady=6, ipady=8)
        ttk.Button(self, text="Log out", command=self.logout).pack(anchor="w", pady=20)

    def on_show(self):
        self.greeting.config(text=f"Logged in as: {self.app.doctor}")

    def logout(self):
        self.app.doctor = ""
        self.app.show("LoginScreen")


# ---------------- 2b. library ----------------
class LibraryScreen(Screen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.heading("Trial library", "Search past PEEP trials by patient number.")

        bar = ttk.Frame(self)
        bar.pack(fill="x")
        self.query = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.query, width=30)
        entry.pack(side="left")
        entry.bind("<Return>", lambda e: self.search())
        ttk.Button(bar, text="Search", command=self.search).pack(side="left", padx=8)

        self.tree = ttk.Treeview(self, columns=("id", "patient", "doctor", "date", "steps"),
                                 show="headings", height=8)
        for col, title, width in (("id", "ID", 50), ("patient", "Patient", 140),
                                  ("doctor", "Doctor", 140), ("date", "Date", 170),
                                  ("steps", "Steps", 60)):
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="center")
        self.tree.pack(fill="x", pady=12)
        self.tree.bind("<<TreeviewSelect>>", self.show_details)

        self.details = tk.Text(self, height=12, wrap="word", state="disabled",
                               bg="white", fg=TEXT, relief="flat", padx=10, pady=8)
        self.details.pack(fill="both", expand=True)
        ttk.Button(self, text="Back", command=lambda: app.show("WelcomeScreen")
                   ).pack(anchor="w", pady=(12, 0))

    def on_show(self):
        self.query.set("")
        self.search()

    def search(self):
        self.tree.delete(*self.tree.get_children())
        for r in db.search_trials(self.query.get().strip()):
            self.tree.insert("", "end", values=(r["id"], r["patient_number"], r["doctor"],
                                                r["created_at"], r["n_steps"]))
        self._set_details("")

    def show_details(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        trial_id = int(self.tree.item(selected[0])["values"][0])
        t, steps = db.get_trial(trial_id), db.get_steps(trial_id)
        v = show_value
        lines = [
            f"Patient {t['patient_number']}   |   Doctor: {t['doctor']}   |   {t['created_at']}",
            f"PaO2/FiO2: {v(t['pao2_fio2'])} mmHg   |   Protocol initial PEEP: {v(t['initial_peep'])} cmH2O",
            f"Baseline: PEEP {v(t['peep'])}, FiO2 {v(t['fio2'])} %, VT {v(t['tidal_volume'])} mL, "
            f"RR {v(t['respiratory_rate'])}/min, Pplat {v(t['plateau_pressure'])}, "
            f"SpO2 {v(t['spo2'])} %, position {v(t['patient_position'])}",
            f"Notes: {v(t['notes'])}",
            "",
            "PEEP steps:" if steps else "No PEEP steps recorded for this trial.",
        ]
        for s in steps:
            lines.append(f"  Step {s['step_number']}: PEEP {s['peep']:g}, Pplat {s['p_plateau']:g}, "
                         f"EIT file: {os.path.basename(s['eit_file'] or '-')}")
        self._set_details("\n".join(lines))

    def _set_details(self, text):
        self.details.config(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", text)
        self.details.config(state="disabled")


# ---------------- 3. patient data and baseline ----------------
FIELDS = [  # (label, key)
    ("Patient number *", "patient_number"),
    ("PaO2 (mmHg) *", "pao2"),
    ("FiO2 (%) *", "fio2"),
    ("Current PEEP (cmH2O) *", "peep"),
    ("Tidal volume (mL) *", "tidal_volume"),
    ("Respiratory rate (/min) *", "respiratory_rate"),
    ("Plateau pressure (cmH2O)", "plateau_pressure"),
    ("SpO2 (%)", "spo2"),
]
REQUIRED = {"patient_number", "pao2", "fio2", "peep", "tidal_volume", "respiratory_rate"}
POSITIONS = ("Supine", "Prone", "Left lateral", "Right lateral", "Other")


class BaselineScreen(Screen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.heading("Start PEEP trial", "Record patient data and baseline measurements. * = required.")

        self.vars = {key: tk.StringVar() for _, key in FIELDS}
        self.position = tk.StringVar()
        self.eit_file = tk.StringVar()
        self.notes = tk.StringVar()

        grid = ttk.Frame(self)
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1)
        for i, (label, key) in enumerate(FIELDS):
            cell = ttk.Frame(grid)
            cell.grid(row=i // 2, column=i % 2, sticky="ew", padx=(0, 14), pady=6)
            ttk.Label(cell, text=label).pack(anchor="w")
            ttk.Entry(cell, textvariable=self.vars[key]).pack(fill="x")

        ttk.Label(self, text="Patient position").pack(anchor="w", pady=(10, 0))
        ttk.Combobox(self, textvariable=self.position, values=POSITIONS,
                     state="readonly", width=24).pack(anchor="w")

        ttk.Label(self, text="Baseline EIT file (optional)").pack(anchor="w", pady=(10, 0))
        row = ttk.Frame(self)
        row.pack(fill="x")
        ttk.Entry(row, textvariable=self.eit_file, state="readonly").pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Browse...", command=self.pick_eit).pack(side="left", padx=8)

        ttk.Label(self, text="Notes").pack(anchor="w", pady=(10, 0))
        ttk.Entry(self, textvariable=self.notes).pack(fill="x")

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=18)
        ttk.Button(buttons, text="Continue", command=self.continue_).pack(side="right")
        ttk.Button(buttons, text="Back", command=lambda: app.show("WelcomeScreen")
                   ).pack(side="right", padx=8)

    def on_show(self):  # start with an empty form for every new trial
        for var in (*self.vars.values(), self.eit_file, self.notes):
            var.set("")
        self.position.set("Select position")

    def pick_eit(self):
        path = filedialog.askopenfilename(title="Select EIT file",
                                          filetypes=[("EIT data", "*.eit"), ("All files", "*.*")])
        if path:
            self.eit_file.set(path)

    def continue_(self):
        data = {}
        for label, key in FIELDS:
            text = self.vars[key].get().strip()
            name = label.replace(" *", "")
            if not text:
                if key in REQUIRED:
                    messagebox.showerror("Missing value", f"'{name}' is required.")
                    return
                data[key] = None
            elif key == "patient_number":
                data[key] = text
            else:
                try:
                    data[key] = to_float(text)
                except ValueError:
                    messagebox.showerror("Invalid value", f"'{name}' must be a number.")
                    return

        if data["pao2"] <= 0 or not (21 <= data["fio2"] <= 100):
            messagebox.showerror("Invalid value", "PaO2 must be above 0 and FiO2 between 21 and 100 %.")
            return

        ratio = data["pao2"] / (data["fio2"] / 100)  # FiO2 as a fraction: 40 % -> 0.40
        try:
            initial_peep = get_initial_peep(ratio)
        except ValueError as e:
            messagebox.showerror("Protocol not applicable", str(e))
            return

        data["pao2_fio2"] = ratio
        data["initial_peep"] = initial_peep
        pos = self.position.get()
        data["patient_position"] = pos if pos in POSITIONS else None
        data["eit_file"] = self.eit_file.get() or None
        data["notes"] = self.notes.get().strip() or None

        self.app.begin_trial(data)
        self.app.show("RecommendationScreen")


# ---------------- 4. trial recommendation (placeholder) ----------------
class RecommendationScreen(Screen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.heading("Trial recommendation", "Placeholder until the prediction model is ready.")
        self.summary = ttk.Label(self, text="", font=("Arial", 12), justify="left")
        self.summary.pack(anchor="w", pady=(0, 16))
        ttk.Label(self, text="Prediction model: no recommendation available yet.",
                  foreground=MUTED).pack(anchor="w")

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=24)
        ttk.Button(buttons, text="Start PEEP steps",
                   command=lambda: app.show("StepsScreen")).pack(side="right")
        ttk.Button(buttons, text="Cancel", command=lambda: app.show("WelcomeScreen")
                   ).pack(side="right", padx=8)

    def on_show(self):
        a = self.app
        self.summary.config(text=(
            f"Patient: {a.baseline['patient_number']}\n"
            f"PaO2/FiO2: {a.baseline['pao2_fio2']:.0f} mmHg\n"
            f"Protocol initial PEEP: {a.baseline['initial_peep']} cmH2O\n"
            f"PEEP sequence: {' -> '.join(str(p) for p in a.sequence)} cmH2O"))


# ---------------- 5. PEEP steps and EIT measurements ----------------
class StepsScreen(Screen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.heading("PEEP steps and EIT measurements")

        self.peep = tk.StringVar()
        self.p_plateau = tk.StringVar()
        self.eit_file = tk.StringVar()
        self.lowpass = tk.StringVar()
        self.num_breaths = tk.StringVar()
        self.remaining = 0
        self.timer_running = False
        self.timer_finished = False
        self.busy = False
        self._job = None

        f2 = ttk.LabelFrame(self, text="Settings (defaults from constant_dictionary)")
        f2.pack(fill="x", pady=6)
        ttk.Label(f2, text="Lowpass cutoff (Hz)").grid(row=0, column=0, padx=8, pady=6)
        ttk.Entry(f2, textvariable=self.lowpass, width=10).grid(row=0, column=1, padx=8)
        ttk.Label(f2, text="Breaths to average").grid(row=0, column=2, padx=8)
        ttk.Entry(f2, textvariable=self.num_breaths, width=10).grid(row=0, column=3, padx=8)

        f3 = ttk.LabelFrame(self, text="Current PEEP step")
        f3.pack(fill="x", pady=6)
        self.step_label = ttk.Label(f3, text="", font=("Arial", 13, "bold"))
        self.step_label.grid(row=0, column=0, columnspan=5, sticky="w", padx=8, pady=(8, 4))
        self.timer_label = ttk.Label(f3, text="", font=("Arial", 20))
        self.timer_label.grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.timer_btn = ttk.Button(f3, text="Start 2-minute timer", command=self.start_timer)
        self.timer_btn.grid(row=1, column=1, padx=8)
        self.skip_btn = ttk.Button(f3, text="Skip timer", command=self.skip_timer)
        self.skip_btn.grid(row=1, column=2, padx=8)

        ttk.Label(f3, text="PEEP used (cmH2O) *").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(f3, textvariable=self.peep, width=12).grid(row=2, column=1, padx=8)
        ttk.Label(f3, text="Plateau pressure (cmH2O) *").grid(row=2, column=2, sticky="w", padx=8)
        ttk.Entry(f3, textvariable=self.p_plateau, width=12).grid(row=2, column=3, padx=8)
        ttk.Label(f3, text="EIT file *").grid(row=3, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(f3, textvariable=self.eit_file, state="readonly", width=45
                  ).grid(row=3, column=1, columnspan=3, sticky="ew", padx=8)
        ttk.Button(f3, text="Browse...", command=self.pick_eit).grid(row=3, column=4, padx=8)

        self.save_btn = ttk.Button(f3, text="Save step and run EIDORS", command=self.add_step)
        self.save_btn.grid(row=4, column=0, columnspan=2, sticky="w", padx=8, pady=10)
        self.progress = ttk.Progressbar(f3, mode="indeterminate", length=200)
        self.progress.grid(row=4, column=2, columnspan=2, padx=8)
        self.status = ttk.Label(f3, text="")
        self.status.grid(row=5, column=0, columnspan=5, sticky="w", padx=8, pady=(0, 6))

        f4 = ttk.LabelFrame(self, text="Steps recorded so far")
        f4.pack(fill="both", expand=True, pady=6)
        self.table = ttk.Treeview(f4, columns=("step", "peep", "pplat", "frames"),
                                  show="headings", height=6)
        for col, title in (("step", "Step"), ("peep", "PEEP"),
                           ("pplat", "P plateau"), ("frames", "EIT frames")):
            self.table.heading(col, text=title)
            self.table.column(col, width=100, anchor="center")
        self.table.pack(fill="both", expand=True, padx=8, pady=8)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", pady=6)
        ttk.Button(bottom, text="Finish trial", command=self.finish).pack(side="right")
        ttk.Button(bottom, text="Leave trial", command=self.leave).pack(side="right", padx=8)

    def on_show(self):
        self.table.delete(*self.table.get_children())
        self.lowpass.set(str(constant_dictionary["lowpass_cutoff"]))
        self.num_breaths.set(str(constant_dictionary["num_breaths_to_average"]))
        self.busy = False
        self.status.config(text="")
        self.show_current_step()

    # ----- which buttons can be clicked -----
    def update_controls(self):
        active = self.app.step_index < len(self.app.sequence)

        def enable(widget, on):
            widget.state(["!disabled"] if on else ["disabled"])

        enable(self.timer_btn, active and not self.timer_running and not self.timer_finished and not self.busy)
        enable(self.skip_btn, active and self.timer_running)
        enable(self.save_btn, active and self.timer_finished and not self.busy)

    def show_current_step(self):
        a = self.app
        self.timer_running = False
        self.timer_finished = False
        self.p_plateau.set("")
        self.eit_file.set("")
        if a.step_index >= len(a.sequence):
            self.step_label.config(text="PEEP trial sequence completed. Press 'Finish trial'.")
            self.timer_label.config(text="")
            self.peep.set("")
        else:
            peep = a.sequence[a.step_index]
            self.step_label.config(
                text=f"Step {a.step_index + 1} of {len(a.sequence)}: "
                     f"set PEEP to {peep} cmH2O and maintain for 2 minutes")
            self.peep.set(str(peep))  # pre-filled, the doctor can correct it
            self.timer_label.config(text=self.fmt(STEP_SECONDS))
        self.update_controls()

    # ----- timer -----
    @staticmethod
    def fmt(seconds):
        return "%02d:%02d" % divmod(seconds, 60)

    def start_timer(self):
        self.timer_running = True
        self.remaining = STEP_SECONDS
        self.update_controls()
        self.tick()

    def tick(self):
        self.timer_label.config(text=self.fmt(self.remaining))
        if self.remaining <= 0:
            self.timer_done()
        else:
            self.remaining -= 1
            self._job = self.after(1000, self.tick)  # run tick again in 1 second

    def timer_done(self):
        self.timer_running = False
        self.timer_finished = True
        self.status.config(text="Step time finished. Enter the plateau pressure and select the EIT file.")
        self.update_controls()

    def skip_timer(self):
        self.cancel_timer()
        self.timer_done()

    def cancel_timer(self):
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None

    # ----- saving a step -----
    def pick_eit(self):
        path = filedialog.askopenfilename(title="Select EIT file",
                                          filetypes=[("EIT data", "*.eit"), ("All files", "*.*")])
        if path:
            self.eit_file.set(path)

    def add_step(self):
        try:
            peep, pplat = to_float(self.peep.get()), to_float(self.p_plateau.get())
        except ValueError:
            messagebox.showerror("Invalid input", "PEEP and plateau pressure must be numbers.")
            return
        if pplat <= peep:
            messagebox.showerror("Invalid input", "Plateau pressure must be higher than PEEP.")
            return
        path = self.eit_file.get()
        if not path:
            messagebox.showerror("Missing file", "Please select an EIT file.")
            return

        self.busy = True
        self.progress.start(10)
        self.status.config(text="Running MATLAB/EIDORS... this can take a while.")
        self.update_controls()

        def worker():  # runs in the background so the window does not freeze
            try:
                imgs, time = run_eidors(path)
                self.after(0, lambda: self.step_done(peep, pplat, path, imgs, time))
            except Exception as e:
                msg = str(e)
                self.after(0, lambda: self.step_failed(msg))

        threading.Thread(target=worker, daemon=True).start()

    def step_done(self, peep, pplat, path, imgs, time):
        a = self.app
        a.trial_data_value["PEEP"].append(peep)
        a.trial_data_value["p_plateau"].append(pplat)
        a.trial_data_frames["Eidors_imgs"].append(imgs)
        a.trial_data_frames["Eidors_time"].append(time)

        n = len(a.trial_data_value["PEEP"])
        db.add_step(a.trial_id, n, peep, pplat, path)  # save the inputs in the library
        self.table.insert("", "end", values=(n, peep, pplat, len(time)))

        self.busy = False
        self.progress.stop()
        next_peep = get_next_peep(a.sequence, a.step_index)
        a.step_index += 1
        self.show_current_step()
        self.status.config(text="Step saved." +
                           (f" Next recommended PEEP: {next_peep} cmH2O" if next_peep else ""))

    def step_failed(self, msg):
        self.busy = False
        self.progress.stop()
        self.status.config(text="")
        self.update_controls()
        messagebox.showerror("EIDORS failed", msg)

    # ----- leaving -----
    def finish(self):
        if len(self.app.trial_data_value["PEEP"]) < 2:
            messagebox.showwarning("Not enough steps", "Record at least 2 PEEP steps first.")
            return
        try:
            constant_dictionary["lowpass_cutoff"] = float(self.lowpass.get())
            constant_dictionary["num_breaths_to_average"] = int(self.num_breaths.get())
        except ValueError:
            messagebox.showerror("Invalid settings", "Check the lowpass cutoff and number of breaths.")
            return

        # LATER: call the backend calculations here
        # (extract_minmax_breath_frames, compliance_matrix, collapse_berekenen, ...)
        messagebox.showinfo("Input complete",
                            "Inputs stored and saved in the library.\n"
                            "Backend calculations will be connected here.")
        self.cancel_timer()
        self.app.show("WelcomeScreen")

    def leave(self):
        if self.busy:
            messagebox.showwarning("Busy", "Wait until EIDORS has finished.")
            return
        if messagebox.askyesno("Leave trial", "Leave this trial? Steps already saved stay in the library."):
            self.cancel_timer()
            self.app.show("WelcomeScreen")


if __name__ == "__main__":
    db.init_db()   # creates the database file and tables the first time
    App().mainloop()