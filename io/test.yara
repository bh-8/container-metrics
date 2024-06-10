import "console"

rule my_rule : main {
    condition:
        console.log("test.yara: Hello, World @ ", filename)
}
