# journey.py
# FinPath Journey Twin

JOURNEY_STEPS = {
    "Insurance Claim": [
        "Understand policy",
        "Collect required documents",
        "Submit claim",
        "Track claim status",
        "Complete claim process"
    ],

    "Loan Planning": [
        "Define loan requirement",
        "Compare loan options",
        "Calculate EMI",
        "Review repayment plan",
        "Finalize loan decision"
    ],

    "Savings": [
        "Track income",
        "Track expenses",
        "Create monthly budget",
        "Set savings target",
        "Review savings progress"
    ],

    "Investment": [
        "Define investment goal",
        "Understand risk tolerance",
        "Choose investment approach",
        "Review investment plan",
        "Monitor investment progress"
    ]
}


class FinancialJourney:
    """
    Manages a user's financial planning journey.
    """

    def __init__(self):
        self.goal = None
        self.completed = []

    def start(self, goal):
        """
        Start a new financial journey.
        """
        if goal not in JOURNEY_STEPS:
            raise ValueError("Invalid journey goal")

        self.goal = goal
        self.completed = []

        return self.get_status()

    def get_steps(self):
        """
        Return the steps for the current journey.
        """
        if not self.goal:
            return []

        return JOURNEY_STEPS.get(self.goal, [])

    def complete_step(self, step):
        """
        Mark a journey step as completed.
        """
        if not self.goal:
            raise ValueError("No journey has been started")

        if step not in self.get_steps():
            raise ValueError("Invalid journey step")

        if step not in self.completed:
            self.completed.append(step)

        return self.get_status()

    def reset(self):
        """
        Reset the current journey.
        """
        self.goal = None
        self.completed = []

        return self.get_status()

    def get_status(self):
        """
        Return the current journey status.
        """
        steps = self.get_steps()
        total_steps = len(steps)
        completed_count = len(self.completed)

        if total_steps > 0:
            progress = int((completed_count / total_steps) * 100)
        else:
            progress = 0

        if not self.goal:
            status = "Not Started"
        elif progress == 100:
            status = "Completed"
        elif completed_count > 0:
            status = "In Progress"
        else:
            status = "Started"

        next_step = None

        for step in steps:
            if step not in self.completed:
                next_step = step
                break

        return {
            "goal": self.goal,
            "status": status,
            "progress": progress,
            "total_steps": total_steps,
            "completed_count": completed_count,
            "steps": steps,
            "completed": self.completed,
            "next_step": next_step
        }