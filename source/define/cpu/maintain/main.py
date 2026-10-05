import sys

import logical_core_number
import cacheline
def main():
    file_path = sys.argv[1]
    file = open(file_path, 'w', encoding='utf-8')

    def once_write():
        file.write("#pragma once\n\n")
        return
    once_write()

    def logical_core_number_write():
        res = logical_core_number.get()
        error = logical_core_number.check(res)
        if error == False :
            sys.exit(1)
        file.write("#define DESTINY_PYTHON_DEFINE_CPU_LOGICAL_CORE_NUMBER " + res + '\n')
        return
    logical_core_number_write()

    def cacheline_write():
        res = cacheline.get()
        error = cacheline.check(res)
        if error == False:
            sys.exit(1)
        file.write("#define DESTINY_PYTHON_DEFINE_CPU_CACHELINE " + res + '\n')
        return
    cacheline_write()

    return

if __name__ == '__main__':
    main()