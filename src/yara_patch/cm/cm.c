#include <stdio.h>
#include <stdlib.h>
#include <yara/modules.h>
#include <mongoc/mongoc.h>
#include <bson/bson.h>

#define MODULE_NAME cm
#define BUFFER_SIZE 16384

// https://stackoverflow.com/questions/656542/trim-a-string-in-c
char* ltrim(char *s) {
    while(isspace(*s)) s++;
    return s;
}
char* rtrim(char *s) {
    char* back = s + strlen(s);
    while(isspace(*--back));
    *(back+1) = '\0';
    return s;
}
char* trim(char *s) {
    return rtrim(ltrim(s)); 
}

char* get_document_as_json(const char* connection_str, const char* db_name, const char* collection_name, const char* mongodb_identifier) {
    const bson_t* bson_doc;
    bson_oid_t oid;
    bson_error_t error;

    mongoc_init();
    mongoc_uri_t* uri = mongoc_uri_new_with_error(connection_str, &error);
    if(!uri)
        return "<E:MONGO_URI>";

    mongoc_client_t* client = mongoc_client_new_from_uri(uri);
    if(!client)
        return "<E:MONGO_CLIENT>";

    mongoc_collection_t* collection = mongoc_client_get_collection(client, db_name, collection_name);
    if(!collection)
        return "<E:MONGO_COLLECTION>";

    // build query for document by object id
    bson_oid_init_from_string(&oid, mongodb_identifier);
    bson_t* primary_key_query = BCON_NEW("_id", BCON_OID(&oid));

    // execute query
    mongoc_cursor_t* cursor = mongoc_collection_find_with_opts(collection, primary_key_query, NULL, NULL);

    char* json_str;
    while(mongoc_cursor_next(cursor, &bson_doc)) {
        json_str = bson_as_json(bson_doc, NULL);
        break;
    }

    bson_free(primary_key_query);
    mongoc_cursor_destroy(cursor);
    mongoc_collection_destroy(collection);
    mongoc_client_destroy(client);
    mongoc_uri_destroy(uri);
    mongoc_cleanup();

    return json_str;
}

char* execute_jp(const char* json, const char* jmes_query) {
    FILE *write_fp, *read_fp;
    char buffer[BUFFER_SIZE];
    char *output = NULL;
    size_t output_size = 0;
    char command[BUFFER_SIZE];
    int pipe_stdin[2], pipe_stdout[2];
    pid_t pid;

    // Construct the command string with the argument
    snprintf(command, sizeof(command), "/home/container-metrics/jp --compact --unquoted \"%s\"", jmes_query);

    // Create pipes for stdin and stdout
    pipe(pipe_stdin);
    pipe(pipe_stdout);

    // Fork the process
    pid = fork();
    if (pid == -1) {
        perror("fork");
        return NULL;
    } else if (pid == 0) { // Child process
        // Redirect stdin and stdout
        dup2(pipe_stdin[0], STDIN_FILENO);
        dup2(pipe_stdout[1], STDOUT_FILENO);

        // Close unused pipe ends
        close(pipe_stdin[1]);
        close(pipe_stdout[0]);

        // Execute the command
        execl("/bin/sh", "sh", "-c", command, (char *) NULL);
        perror("execl");
        exit(EXIT_FAILURE);
    } else { // Parent process
        // Close unused pipe ends
        close(pipe_stdin[0]);
        close(pipe_stdout[1]);

        // Write JSON data to the child process
        write(pipe_stdin[1], json, strlen(json));
        close(pipe_stdin[1]); // Close write end of stdin pipe

        // Open a stream to read the output from the child process
        read_fp = fdopen(pipe_stdout[0], "r");
        if (read_fp == NULL) {
            perror("fdopen");
            return NULL;
        }

        // Read the output from the process
        while (fgets(buffer, sizeof(buffer), read_fp) != NULL) {
            size_t buffer_len = strlen(buffer);
            output = realloc(output, output_size + buffer_len + 1);
            if (output == NULL) {
                perror("realloc");
                fclose(read_fp);
                return NULL;
            }
            strcpy(output + output_size, buffer);
            output_size += buffer_len;
        }

        // Close the read stream
        fclose(read_fp);

        // Wait for the child process to finish
        wait(NULL);
    }
    return output;
}

char* jmesq(char* mdb_uri, char* mdb_db, char* mdb_c, char* mdb_oid, char* jmes_query) {
    char* json = get_document_as_json(mdb_uri, mdb_db, mdb_c, mdb_oid);
    if(!json)
        return "<cm.c:jmesq:JSON_NULL>";

    char *jp = execute_jp(json, jmes_query);
    if(!jp)
        return "<cm.c:jmesq:JP_NULL>";

    return rtrim(jp);
}

define_function(jmesq_s) {
    char* mdb_uri = string_argument(1);
    char* mdb_db = string_argument(2);
    char* mdb_c = string_argument(3);
    char* mdb_oid = string_argument(4);
    char* jmes_query = string_argument(5);

    char* query_result = jmesq(mdb_uri, mdb_db, mdb_c, mdb_oid, jmes_query);
    return_string(query_result);
}

define_function(jmesq_i) {
    char* mdb_uri = string_argument(1);
    char* mdb_db = string_argument(2);
    char* mdb_c = string_argument(3);
    char* mdb_oid = string_argument(4);
    char* jmes_query = string_argument(5);

    char* query_result = jmesq(mdb_uri, mdb_db, mdb_c, mdb_oid, jmes_query);
    if(strcmp(query_result, "null") == 0)
        return_integer(0);
    int v;
    sscanf(query_result, "%d", &v);
    return_integer(v);
}

define_function(jmesq_f) {
    char* mdb_uri = string_argument(1);
    char* mdb_db = string_argument(2);
    char* mdb_c = string_argument(3);
    char* mdb_oid = string_argument(4);
    char* jmes_query = string_argument(5);

    char* query_result = jmesq(mdb_uri, mdb_db, mdb_c, mdb_oid, jmes_query);
    if(strcmp(query_result, "null") == 0)
        return_float(0);
    float v;
    sscanf(query_result, "%f", &v);
    return_float(v);
}

begin_declarations;
    declare_function("jmesq_s", "sssss", "s", jmesq_s);
    declare_function("jmesq_i", "sssss", "i", jmesq_i);
    declare_function("jmesq_f", "sssss", "f", jmesq_f);
end_declarations;

int module_initialize(YR_MODULE* module) {
    return ERROR_SUCCESS;
}

int module_finalize(YR_MODULE* module) {
    return ERROR_SUCCESS;
}

int module_load(YR_SCAN_CONTEXT* context, YR_OBJECT* module_object, void* module_data, size_t module_data_size) {
    return ERROR_SUCCESS;
}

int module_unload(YR_OBJECT* module_object) {
    return ERROR_SUCCESS;
}

#undef MODULE_NAME
