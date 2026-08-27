# destinyTest: bootstrap test application. Verifies the module chain
# (define + basicType) works. Application modules build executables
# and explicitly link the module libraries they depend on.
destiny_add_application()
target_link_libraries(apps_destinyTest PRIVATE basicType)
