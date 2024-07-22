import "console"
import "cm"

rule example_rule : main {
    condition:
        console.log("test.yara: Hello, World @ ", cm.jmesq_s("mongodb://admin:admin@mongo-db:27017", "2024-07-22", "test", mdb_oid, "meta.file.name"))
}
