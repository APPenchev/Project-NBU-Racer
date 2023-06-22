
global_variables = {}

def save_options(path):
    global global_variables
    with open(path, "w") as file:
        file.truncate()

    with open(path, 'a') as file:
        file.flush()
        for k,i in global_variables.items():
            if isinstance(i, dict):
                file.write(f'${k}=')
                for e, (k_, i_) in enumerate(i.items()):
                    file.write(f'{k_},{i_}')
                    if e != len(i.items()) - 1:
                        file.write(',')
                    else:
                        file.write('\n')


            else:
                file.write(f'%{k}=')
                for e,k_ in enumerate(i):
                    file.write(f'{k_}')
                    if e != len(i) - 1:
                        file.write(',')
                    else:
                        file.write('\n')


def parse_options(path):
    global global_variables
    options = {}
    with open(path, 'r') as file:
        for line in file.readlines():
            if line.startswith('$'):
                u = line[1:]
                u = u.split('=')

                key = u[0]
                options[key] = {}
                parts = u[1].split(',')
                for i in range(0, len(parts), 2):
                    options[key][parts[i]] = parts[i + 1].rstrip()

            if line.startswith('%'):
                u = line[1:]
                u = u.split('=')

                key = u[0]
                options[key] = []
                parts = u[1].split(',')
                for i in parts:
                    options[key].append(i.rstrip())

    global_variables = options