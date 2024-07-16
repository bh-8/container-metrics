import "console"
import "cm"

rule example_rule : main {
    condition:
        console.log("test.yara: Hello, World @ ", cm.jmesq("mongodb://admin:admin@mongo-db:27017", "2024-07-16", "test", mdb_oid, "meta.file.name"))
}
