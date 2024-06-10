#include <yara/modules.h>
#include <mongoc/mongoc.h>

#define MODULE_NAME cm

begin_declarations;
    declare_string("greeting");
end_declarations;

int module_initialize(YR_MODULE* module) {
    return ERROR_SUCCESS;
}

int module_finalize(YR_MODULE* module) {
    return ERROR_SUCCESS;
}

int module_load(YR_SCAN_CONTEXT* context, YR_OBJECT* module_object, void* module_data, size_t module_data_size) {
    yr_set_string("Hello World!", module_object, "greeting");
    return ERROR_SUCCESS;
}

int module_unload(YR_OBJECT* module_object) {
    return ERROR_SUCCESS;
}

#undef MODULE_NAME
