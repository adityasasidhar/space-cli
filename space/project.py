"""
Project detection and test runner for Space CLI.
"""
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class ProjectDetector:
    """Detect project type and analyze structure."""
    
    # Project type indicators
    INDICATORS = {
        "python": {
            "files": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile", "poetry.lock"],
            "extensions": [".py"],
            "test_command": "pytest",
            "test_patterns": ["test_*.py", "*_test.py", "tests/"]
        },
        "node": {
            "files": ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
            "extensions": [".js", ".ts", ".jsx", ".tsx"],
            "test_command": "npm test",
            "test_patterns": ["*.test.js", "*.spec.js", "__tests__/"]
        },
        "rust": {
            "files": ["Cargo.toml", "Cargo.lock"],
            "extensions": [".rs"],
            "test_command": "cargo test",
            "test_patterns": ["tests/"]
        },
        "go": {
            "files": ["go.mod", "go.sum"],
            "extensions": [".go"],
            "test_command": "go test ./...",
            "test_patterns": ["*_test.go"]
        },
        "ruby": {
            "files": ["Gemfile", "Gemfile.lock", "Rakefile"],
            "extensions": [".rb"],
            "test_command": "bundle exec rspec",
            "test_patterns": ["spec/", "test/"]
        }
    }
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir).resolve()
    
    def detect_type(self) -> Dict[str, Any]:
        """Detect project type based on indicator files."""
        detected_types = []
        
        for proj_type, indicators in self.INDICATORS.items():
            score = 0
            for indicator_file in indicators["files"]:
                if (self.project_dir / indicator_file).exists():
                    score += 10
            
            # Check for file extensions
            for ext in indicators["extensions"]:
                if list(self.project_dir.glob(f"**/*{ext}"))[:1]:
                    score += 5
                    break
            
            if score > 0:
                detected_types.append((proj_type, score))
        
        # Sort by score descending
        detected_types.sort(key=lambda x: x[1], reverse=True)
        
        if detected_types:
            primary = detected_types[0][0]
            return {
                "type": primary,
                "confidence": detected_types[0][1],
                "all_detected": [t[0] for t in detected_types],
                "test_command": self.INDICATORS[primary]["test_command"]
            }
        
        return {
            "type": "unknown",
            "confidence": 0,
            "all_detected": [],
            "test_command": None
        }
    
    def find_entry_points(self) -> List[str]:
        """Find common entry point files."""
        entry_points = []
        common_names = [
            "main.py", "app.py", "index.py", "__main__.py",
            "index.js", "main.js", "app.js", "server.js",
            "main.go", "main.rs", "lib.rs"
        ]
        
        for name in common_names:
            found = list(self.project_dir.rglob(name))
            entry_points.extend([str(f.relative_to(self.project_dir)) for f in found[:3]])
        
        return entry_points[:10]
    
    def parse_dependencies(self) -> Dict[str, Any]:
        """Parse project dependencies."""
        deps = {"dependencies": [], "dev_dependencies": []}
        
        # Python: requirements.txt
        req_file = self.project_dir / "requirements.txt"
        if req_file.exists():
            with open(req_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        deps["dependencies"].append(line.split("==")[0].split(">=")[0])
        
        # Python: pyproject.toml
        pyproject = self.project_dir / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                    project_deps = data.get("project", {}).get("dependencies", [])
                    deps["dependencies"].extend(project_deps)
            except:
                pass
        
        # Node: package.json
        pkg_json = self.project_dir / "package.json"
        if pkg_json.exists():
            try:
                with open(pkg_json) as f:
                    data = json.load(f)
                    deps["dependencies"] = list(data.get("dependencies", {}).keys())
                    deps["dev_dependencies"] = list(data.get("devDependencies", {}).keys())
            except:
                pass
        
        return deps
    
    def analyze_project(self) -> Dict[str, Any]:
        """Full project analysis."""
        proj_type = self.detect_type()
        
        return {
            **proj_type,
            "entry_points": self.find_entry_points(),
            "dependencies": self.parse_dependencies(),
            "project_dir": str(self.project_dir)
        }


class TestRunner:
    """Discover and run tests for various project types."""
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir).resolve()
        self.detector = ProjectDetector(project_dir)
    
    def discover_tests(self) -> Dict[str, Any]:
        """Discover test files in the project."""
        proj_info = self.detector.detect_type()
        proj_type = proj_info.get("type", "unknown")
        
        test_files = []
        
        if proj_type == "python":
            # Find pytest-style tests
            patterns = ["test_*.py", "*_test.py"]
            for pattern in patterns:
                test_files.extend(str(f) for f in self.project_dir.rglob(pattern))
            
            # Check for tests/ directory
            tests_dir = self.project_dir / "tests"
            if tests_dir.exists():
                test_files.extend(str(f) for f in tests_dir.rglob("*.py"))
        
        elif proj_type == "node":
            patterns = ["*.test.js", "*.spec.js", "*.test.ts", "*.spec.ts"]
            for pattern in patterns:
                test_files.extend(str(f) for f in self.project_dir.rglob(pattern))
        
        elif proj_type == "go":
            test_files.extend(str(f) for f in self.project_dir.rglob("*_test.go"))
        
        elif proj_type == "rust":
            tests_dir = self.project_dir / "tests"
            if tests_dir.exists():
                test_files.extend(str(f) for f in tests_dir.rglob("*.rs"))
        
        return {
            "project_type": proj_type,
            "test_command": proj_info.get("test_command"),
            "test_files": list(set(test_files))[:50],
            "test_count": len(set(test_files))
        }
    
    def run_tests(self, test_path: str = None, verbose: bool = True) -> Dict[str, Any]:
        """Run tests and capture results.
        
        Args:
            test_path: Optional specific test file/directory
            verbose: Include verbose output
        """
        proj_info = self.detector.detect_type()
        proj_type = proj_info.get("type", "unknown")
        
        # Build command based on project type
        if proj_type == "python":
            cmd = ["pytest"]
            if verbose:
                cmd.append("-v")
            if test_path:
                cmd.append(test_path)
        
        elif proj_type == "node":
            cmd = ["npm", "test"]
            if test_path:
                cmd.extend(["--", test_path])
        
        elif proj_type == "go":
            cmd = ["go", "test"]
            if verbose:
                cmd.append("-v")
            cmd.append(test_path if test_path else "./...")
        
        elif proj_type == "rust":
            cmd = ["cargo", "test"]
            if test_path:
                cmd.extend(["--", test_path])
        
        else:
            return {
                "success": False,
                "error": f"Unknown project type: {proj_type}",
                "output": ""
            }
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                "success": result.returncode == 0,
                "command": " ".join(cmd),
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "output": result.stdout + ("\n" + result.stderr if result.stderr else "")
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test execution timed out (5 min limit)",
                "command": " ".join(cmd),
                "output": ""
            }
        except FileNotFoundError as e:
            return {
                "success": False,
                "error": f"Test runner not found: {e}",
                "command": " ".join(cmd),
                "output": ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": " ".join(cmd),
                "output": ""
            }


# Tool functions for agent integration
def analyze_project(directory: str = ".") -> str:
    """Analyze project type, dependencies, and structure."""
    try:
        detector = ProjectDetector(directory)
        result = detector.analyze_project()
        
        output = f"Project Analysis for: {result['project_dir']}\n"
        output += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        output += f"Type: {result['type']} (confidence: {result['confidence']})\n"
        
        if result.get('test_command'):
            output += f"Test Command: {result['test_command']}\n"
        
        if result.get('entry_points'):
            output += f"\nEntry Points:\n"
            for ep in result['entry_points'][:5]:
                output += f"  • {ep}\n"
        
        deps = result.get('dependencies', {})
        if deps.get('dependencies'):
            output += f"\nDependencies ({len(deps['dependencies'])}):\n"
            for dep in deps['dependencies'][:10]:
                output += f"  • {dep}\n"
            if len(deps['dependencies']) > 10:
                output += f"  ... and {len(deps['dependencies']) - 10} more\n"
        
        return output
    except Exception as e:
        return f"Error analyzing project: {e}"


def run_tests(test_path: str = None, directory: str = ".") -> str:
    """Run project tests and return results."""
    try:
        runner = TestRunner(directory)
        result = runner.run_tests(test_path)
        
        if result.get('error'):
            return f"Error: {result['error']}"
        
        output = f"Test Results ({result.get('command', 'unknown')})\n"
        output += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        output += f"Status: {'✓ PASSED' if result['success'] else '✗ FAILED'}\n"
        output += f"Exit Code: {result.get('exit_code', 'N/A')}\n\n"
        output += result.get('output', '')[:2000]
        
        if len(result.get('output', '')) > 2000:
            output += "\n... (output truncated)"
        
        return output
    except Exception as e:
        return f"Error running tests: {e}"


def discover_tests(directory: str = ".") -> str:
    """Discover test files in the project."""
    try:
        runner = TestRunner(directory)
        result = runner.discover_tests()
        
        output = f"Test Discovery\n"
        output += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        output += f"Project Type: {result['project_type']}\n"
        output += f"Test Command: {result.get('test_command', 'N/A')}\n"
        output += f"Test Files Found: {result['test_count']}\n\n"
        
        if result['test_files']:
            output += "Files:\n"
            for f in result['test_files'][:20]:
                output += f"  • {f}\n"
            if result['test_count'] > 20:
                output += f"  ... and {result['test_count'] - 20} more\n"
        
        return output
    except Exception as e:
        return f"Error discovering tests: {e}"


def find_definition(symbol: str, directory: str = ".") -> str:
    """Find where a symbol (function/class) is defined using grep."""
    try:
        patterns = [
            f"def {symbol}\\(",      # Python function
            f"class {symbol}[:(]",   # Python/JS class
            f"function {symbol}\\(", # JS function
            f"const {symbol} =",     # JS const
            f"func {symbol}\\(",     # Go function
            f"fn {symbol}\\(",       # Rust function
        ]
        
        results = []
        search_path = Path(directory).resolve()
        
        for pattern in patterns:
            try:
                result = subprocess.run(
                    ["grep", "-rn", "-E", pattern, str(search_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.stdout:
                    results.extend(result.stdout.strip().split("\n"))
            except:
                pass
        
        if results:
            output = f"Definition of '{symbol}':\n"
            for r in results[:10]:
                output += f"  {r}\n"
            return output
        else:
            return f"No definition found for '{symbol}'"
    except Exception as e:
        return f"Error finding definition: {e}"


def find_references(symbol: str, directory: str = ".") -> str:
    """Find all references to a symbol."""
    try:
        result = subprocess.run(
            ["grep", "-rn", symbol, str(Path(directory).resolve())],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.stdout:
            lines = result.stdout.strip().split("\n")
            output = f"References to '{symbol}' ({len(lines)} found):\n"
            for line in lines[:30]:
                output += f"  {line}\n"
            if len(lines) > 30:
                output += f"  ... and {len(lines) - 30} more\n"
            return output
        else:
            return f"No references found for '{symbol}'"
    except Exception as e:
        return f"Error finding references: {e}"
