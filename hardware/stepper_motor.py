# hardware/stepper_motor.py
from __future__ import annotations

import threading
import queue
from dataclasses import dataclass
from time import sleep
from typing import Optional

import RPi.GPIO as GPIO


@dataclass
class StepperCommand:
    kind: str               # "move" | "stop"
    forward: bool = True
    steps: int = 0
    delay_s: float = 0.001  # tijd tussen HIGH/LOW


class TB6600Stepper:
    """
    TB6600 step/dir/ena driver via RPi.GPIO.

    - Non-blocking: Flask mag meteen teruggeven, beweging gebeurt in worker thread.
    - Queue: commando's komen achter elkaar, geen overlap.
    - stop(): wist wachtrij + stopt zo snel mogelijk (best-effort).
    """

    def __init__(self, pul_pin: int, dir_pin: int, ena_pin: int, *, bcm_mode: bool = True):
        self.pul = pul_pin
        self.dir = dir_pin
        self.ena = ena_pin

        if bcm_mode:
            GPIO.setmode(GPIO.BCM)
        else:
            GPIO.setmode(GPIO.BOARD)

        GPIO.setup(self.pul, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.dir, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.ena, GPIO.OUT, initial=GPIO.LOW)

        self._cmd_q: "queue.Queue[Optional[StepperCommand]]" = queue.Queue()
        self._stop_flag = threading.Event()
        self._running = True

        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    # ---------- low-level ----------
    def _enable(self):
        GPIO.output(self.ena, GPIO.HIGH)

    def _disable(self):
        GPIO.output(self.ena, GPIO.LOW)

    def _set_direction(self, forward: bool):
        # Jij had: DIR LOW = forward, DIR HIGH = backward
        GPIO.output(self.dir, GPIO.LOW if forward else GPIO.HIGH)

    # ---------- worker ----------
    def _run(self):
        while self._running:
            cmd = self._cmd_q.get()
            if cmd is None:
                break

            try:
                if cmd.kind == "stop":
                    self._stop_flag.set()
                    self._disable()
                    continue

                if cmd.kind == "move":
                    self._execute_move(cmd.forward, cmd.steps, cmd.delay_s)
                    continue

            finally:
                self._cmd_q.task_done()

    def _execute_move(self, forward: bool, steps: int, delay_s: float):
        # reset stop flag voor deze move
        self._stop_flag.clear()

        if steps <= 0:
            return

        # Enable + direction
        self._enable()
        sleep(0.01)
        self._set_direction(forward)
        sleep(0.01)

        # Pulses (best-effort stop: check flag per step)
        for _ in range(steps):
            if self._stop_flag.is_set():
                break
            GPIO.output(self.pul, GPIO.HIGH)
            sleep(delay_s)
            GPIO.output(self.pul, GPIO.LOW)
            sleep(delay_s)

        # Disable na beweging
        self._disable()

    # ---------- public API ----------
    def move(self, *, direction: str, steps: int, delay_s: float):
        """
        direction: "forward" of "backward"
        steps: aantal pulses
        delay_s: seconds tussen high/low
        """
        direction = (direction or "").lower().strip()
        if direction not in ("forward", "backward"):
            raise ValueError("direction must be 'forward' or 'backward'")

        steps = int(steps)
        delay_s = float(delay_s)

        # simpele grenzen (pas gerust aan)
        if steps < 1:
            steps = 1
        if steps > 400000:
            steps = 400000

        # Python is niet realtime; superkleine delays werken vaak niet goed
        if delay_s < 0.0001:
            delay_s = 0.0001
        if delay_s > 0.05:
            delay_s = 0.05

        forward = (direction == "forward")
        self._cmd_q.put(StepperCommand(kind="move", forward=forward, steps=steps, delay_s=delay_s))

    def stop(self):
        """
        Best-effort stop:
        - zet stop_flag zodat lopende move z.s.m. stopt
        - maak wachtrij leeg
        - disable driver
        """
        self._stop_flag.set()

        # queue leegmaken
        while True:
            try:
                item = self._cmd_q.get_nowait()
                if item is None:
                    # laat shutdown token niet weggooien
                    self._cmd_q.put(None)
                    break
                self._cmd_q.task_done()
            except queue.Empty:
                break

        # direct disable + stop command (voor zekerheid)
        self._disable()
        self._cmd_q.put(StepperCommand(kind="stop"))

    def shutdown(self):
        """
        Netjes afsluiten: stopt worker en doet GPIO cleanup.
        """
        self._running = False
        self._stop_flag.set()
        self._disable()
        self._cmd_q.put(None)
        try:
            self._worker.join(timeout=1.0)
        finally:
            GPIO.cleanup()
