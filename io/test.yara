import "console"
import "cm"

rule example_rule : main {
    condition:
        cm.greeting == "Hello World!" and console.log("test.yara: Hello, World @ ", filename)
}
