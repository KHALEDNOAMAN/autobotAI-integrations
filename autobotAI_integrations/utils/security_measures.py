import ast
import re

from autobotAI_integrations.integration_schema import ConnectionTypes


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

# TODO: Add New line compatibility for pattern recognition
SUSPICIOUS_PATTERNS = [
    (r"/dev/tcp", "Detected potential network socket manipulation"),
    (r"/dev/udp", "Detected potential network socket manipulation"),
    (r"nc -e", "Netcat shell redirection pattern detected"),
]


class SecurityAnalyzer(ast.NodeVisitor):
    def __init__(self, check_security=True):
        self.issues = []
        self.check_security = check_security

    def check_code(self, code):
        self.issues = []
        try:
            tree = ast.parse(code)
            self.visit(tree)
            if self.check_security:
                self.check_patterns(code)
        except SyntaxError as e:
            self.issues.append(f"Invalid syntax: {e}")
        return self.issues

    def check_patterns(self, code):
        for pattern, issue in SUSPICIOUS_PATTERNS:
            if re.search(pattern, code):
                self.issues.append(
                    f"Security Warning: '{pattern}', {issue}. This type of operation is restricted"
                )

    def visit_Import(self, node):
        if self.check_security:
            for alias in node.names:
                if alias.name in BANNED_MODULES:
                    self.issues.append(
                        f"Security Restriction: The import '{alias.name}' is not allowed."
                    )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if self.check_security and node.module in BANNED_MODULES:
            self.issues.append(
                f"Security Restriction: The module '{node.module}' is not allowed."
            )
        self.generic_visit(node)

    def visit_Call(self, node):
        if self.check_security:
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in DANGEROUS_FUNCTIONS
            ):
                self.issues.append(
                    f"Security Alert: Restricted function '{node.func.attr}' detected."
                )
            elif (
                isinstance(node.func, ast.Name) and node.func.id in DANGEROUS_FUNCTIONS
            ):
                self.issues.append(
                    f"Security Alert: Restricted function '{node.func.id}' detected."
                )
        self.generic_visit(node)


def validate_code(
    code, connection_type: ConnectionTypes = ConnectionTypes.DIRECT.value
):
    check_security = connection_type != ConnectionTypes.AGENT.value
    analyzer = SecurityAnalyzer(check_security=check_security)
    issues = analyzer.check_code(code)
    if issues:
        raise SecurityError("\n".join(issues))


class SecurityError(Exception):
    pass
