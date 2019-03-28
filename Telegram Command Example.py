import socket
import sys
from time import sleep, time


def all_string(func):
    def decorator(*args, **kwargs):
         args = [str(arg) for arg in args]
         kwargs = {key: str(value) for key, value in kwargs.items()}
         return func(*args, **kwargs)
    return decorator


def isnt_hex(s):
    try:
        int(s, 16)
        return False
    except ValueError:
        return True


def init(msg_list):
    data_init = []
    # Initialization, device data
    for message in msg_list:
        # Send data
        message = b'\x02' + message + b'\x03'
        print(sys.stderr, 'sending "%s"' % message)
        sock.sendall(message)

        # Look for the response
        data = sock.recv(5000)
        print(sys.stderr, 'received "%s"' % data)
        data_ascii = data.decode()[1:-1]
        data_init.append(data_ascii)
        # Error Verification
        erros(data_ascii)
        sleep(0.05)

    return dados


def login(pw='F4724744'):
    if pw.isdigit():
        pw = str(pw)
    message = ('sMI 0 03 ' + pw).encode()
    message = b'\x02' + message + b'\x03'
    print(sys.stderr, 'sending "%s"' % message)
    sock.sendall(message)

    # Look for the response
    data = sock.recv(5000)
    print(sys.stderr, 'received "%s"' % data)
    sleep(0.05)
    # Error Verification
    erros(data)
    if data.decode()[1:-1] == 'sAI 0 1':
        print('Login realizado com sucesso!')
        return data
    else:
        print('Não foi possível realizar o login.')
        return data


def run():
    message = 'sMN Run'.encode()
    message = b'\x02' + message + b'\x03'
    print(sys.stderr, 'sending "%s"' % message)
    sock.sendall(message)

    # Look for the response
    data = sock.recv(5000)
    print(sys.stderr, 'received "%s"' % data)
    sleep(0.05)
    # Error Verification
    erros(data)
    return data


@all_string
def conf(antenna_enable, read_power, write_power, priority, minimum_power_apc, power_inc_apc, dwell_t='64', inventory_rounds='2000', reserved='0'):
    # Login
    entrar = login()
    # Argumentos
    message = ' '.join(['sWN ADconfig0', antenna_enable, dwell_t, read_power, write_power, inventory_rounds, priority, minimum_power_apc, power_inc_apc, reserved])
    message = message.encode()
    message = b'\x02' + message + b'\x03'
    print(sys.stderr, 'sending "%s"' % message)
    sock.sendall(message)

    # Look for the response
    data = sock.recv(5000)
    print(sys.stderr, 'received "%s"' % data)
    sleep(0.05)
    # Error Verification
    erros(data)

    # Sair
    sair = run()
    return data


def inventory(n_antena='F'):
    if n_antena.isdigit():
        n_antena = str(n_antena)
    message = ('sMN IVSingleInv ' + n_antena).encode()
    message = b'\x02' + message + b'\x03'
    print(sys.stderr, 'sending "%s"' % message)
    sock.sendall(message)

    # Look for the response
    data = sock.recv(5000)
    print(sys.stderr, 'received "%s"' % data)
    sleep(0.05)
    # Error Verification
    erros(data)
    return data


def escrever(dados):
    inventario = inventory()
    inventario = inventario.decode()[1:-1]
    n_word = []
    for n, inventario in enumerate(inventario.split()):
        if n == 2 and inventario != '1':
            print('Não há tag no alcance da antena')
            return
        if (n - 4) % 11 == 0:
            n_word.append(int(inventario, 16))

    # Preenche os dados iniciais
    dados = '30' + dados
    modulo = len(dados) % 4
    qtd = len(dados)
    message = 'sMN TAwriteTagData 0 1 2 '
    # Verifica o tamanho dos dados
    maximo = max(n_word) - 4
    if qtd > maximo:
        print(sys.stderr, 'A quantidade de dados é maior do que a capacidade da maior TAG.')
        return
    else:
        dados = dados + '0' * (maximo - qtd)
    qtd = len(dados)
    # Preenche com zeros para o número correto de bits e obtém a quantidade de words
    if modulo != 0:
        dados = dados + '0' * modulo
        word_count = (qtd + (4 - modulo)) // 4
    else:
        word_count = qtd // 4
    # Verifica se é HEX
    if isnt_hex(dados):
        print('Valor não é Hexadecimal')
        return

    # Word count, retry e dados
    message = message + str(word_count) + ' 32 +' + str(qtd) + ' ' + dados
    # Send
    message = b'\x02' + message.encode() + b'\x03'
    print(sys.stderr, 'sending "%s"' % message)
    sock.sendall(message)

    # Look for the response
    data = sock.recv(5000)
    print(sys.stderr, 'received "%s"' % data)
    sleep(0.05)
    # Error Verification
    erros(data)
    return data


def obter_dados(lista):
    lista = lista.decode()[1:-1]
    tags, antenas, rssi, dB, comprimento = ([] for l in range(5))
    i, x = 0, ''
    # Verifica se não está vazia
    if not lista:
        print('Não há dados de Inventário')
        return
    else:
        # Loop nos elementos retornados pela inventory
        for n, elemento in enumerate(lista.split()):
            # print(n, elemento)
            if n == 0 or n == 1 or n == 3:
                continue
            if n == 2 and elemento != '1':
                print('Não há tag no alcance da antena')
                return
            if (n - 4) % 11 == 0:
                comprimento.append(int(elemento, 16))
            if (n - 5) % 11 == 0:
                tags.append(elemento)
            if (n - 6) % 11 == 0:
                antenas.append(elemento)
            if (n - (7 + i)) % 11 == 0:
                x = x + elemento
                i += 1
            if (n - 10) % 11 == 0:
                rssi.append(x)
                i, x = 0, ''
            if (n - (11 + i)) % 11 == 0:
                x = x + elemento
                i += 1
            if (n - 14) % 11 == 0:
                dB.append(x)
                i, x = 0, ''
    return tags, antenas, rssi, dB, comprimento


def erros(err):
    err = err.decode()[1:-1]
    if 'sFA' not in err:
        print('not SFa')
        return
    else:
        err = err.replace('sFA ', '')
    # Trocar o print por tratamento de erros com try except
    if err == '1':
        print('Access Denied')
    elif err == '2' or err == '3':
        print('Unknown Index')
    elif err == '4':
        print('Wrong Condition')
    elif err == '5':
        print('Invalid Data')
    elif err == '6':
        print('Unknown Error')
    elif err == '7':
        print('Too Many Parameter')
    elif err == '8':
        print('Parameter Missing')
    elif err == '9':
        print('Wrong Parameter')
    elif err == 'A':
        print('No Write Access')
    elif err == 'B' or err == 'C':
        print('Unknown Command')
    elif err == 'D':
        print('Server Busy')
    elif err == 'E':
        print('Textstring Too Long')
    elif err == 'F':
        print('Unknown Event')
    elif err == '10':
        print('Too many Parameter')
    elif err == '11':
        print('Invalid Character')
    elif err == '12':
        print('No Message')
    elif err == '13':
        print('No Answer')
    elif err == '14':
        print('Internal Error')
    elif err == '15':
        print('HubAddress: wrong')
    elif err == '16' or err == '17':
        print('HubAddress: error')


start = time()
dados = []

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = ('192.168.0.1', 2112)
print(sys.stderr, 'connecting to %s port %s' % server_address)
sock.connect(server_address)
header = ['ID', 'Type', 'S/N']
inicializacao = [b'sRN DeviceIdent', b'sRN DItype', b'sRN SerialNumber']

try:
    # Dados do dispositivo
    lista_msg = init(inicializacao)
    print(header)
    print(lista_msg)
    # Login e Configuração
    configuracao = conf(1, 'C8', 'E6', 2, 'C8', 'A')
    # Inventário
    inv = inventory()
    # Escrever
    tagWrite = escrever('1111222233334444555566')
    # Obter Dados TAGs
    TAGs, antena, RSSI, antena_power, tag_length = obter_dados(inv)
    print(TAGs, antena, RSSI, antena_power, tag_length)
finally:
    print(sys.stderr, 'closing socket')
    sock.close()

end = time()
print(end - start, 'segundos')
