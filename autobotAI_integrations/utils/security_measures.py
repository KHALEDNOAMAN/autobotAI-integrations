import ast
import re

# Security Configuration
BANNED_MODULES = {
    "os",
    "subprocess",
    "sys",
    "socket",
    "shutil",
    "pty",
    "ctypes",
    "importlib",
    "multiprocessing",
    "pickle",
    "platform",  # Added for system information disclosure prevention
    "asyncio",  # Added for async subprocess potential
}

DANGEROUS_FUNCTIONS = {
    "system",
    "popen",
    "socket",
    "eval",
    "exec",
    "__import__",
    "globals",
    "compile",
    "input",
    "open",  # Added for file system access control
    "reload",  # Added for module reload prevention
}

SUSPICIOUS_PATTERNS = [
    (r"/dev/tcp", "Detected potential network socket manipulation"),
    (r"/dev/udp", "Detected potential network socket manipulation"),
    (r"bash -i", "Possible interactive shell attempt"),
    (r"nc -e", "Netcat shell redirection pattern detected"),
    (r"sh -c", "Shell command injection pattern"),
    (r"python -c", "Potential code injection attempt"),
    (r"curl\s+", "Detected file download utility"),  # Confidence score
    (r"wget\s+", "Detected file download utility"),
]


class SecurityAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.issues = []

    def check_code(self, code):
        self.issues = []
        try:
            tree = ast.parse(code)
            self.visit(tree)
            # NOTE: Disabling Pattern Check for now as some agent based action uses them
            self.check_patterns(code)
        except SyntaxError as e:
            self.issues.append(f"Invalid syntax: {e}")
        return self.issues
    
    def check_patterns(self, code):
        for pattern, issue in SUSPICIOUS_PATTERNS:
            if re.search(pattern, code):
                self.issues.append(f"Security Warning:'{pattern}', {issue}.This type of operation is restricted")

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in BANNED_MODULES:
                self.issues.append(
                    f"Security Restriction: The import '{alias.name}' is not allowed. Please use the predefined import provided in the context object instead."
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module in BANNED_MODULES:
            self.issues.append(
                f"Security Restriction: The module '{node.module}' is not allowed. Please use the predefined modules provided in the context object instead."
            )
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in DANGEROUS_FUNCTIONS:
                self.issues.append(
                    f"Security Alert: Restricted function '{node.func.attr}' detected."
                )
        elif isinstance(node.func, ast.Name):
            if node.func.id in DANGEROUS_FUNCTIONS:
                self.issues.append(
                    f"Security Alert: Restricted function '{node.func.id}' detected."
                )
        self.generic_visit(node)


def validate_code(code):
    analyzer = SecurityAnalyzer()
    issues = analyzer.check_code(code)
    if issues:
        raise SecurityError(", \n".join(issues))


class SecurityError(Exception):
    pass
