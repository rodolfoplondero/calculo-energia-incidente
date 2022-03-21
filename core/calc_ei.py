import numpy as np


def calc_by_ASTM(temperature: list):
    if type(temperature) is not list:
        raise TypeError('Temperature must be a list')

    A = 4.237312
    B = 6.715751
    C = -7.46962
    D = 3.339491
    E = 0.016389

    mmol = 63.546                       # g/mol
    massa = 18                          # g
    diametro = 4                        # cm
    area = np.pi * (diametro / 2) ** 2  # cm^2

    len_temp = len(temperature)

    tk = np.array(temperature)  # Temperatura em Kelvin
    tc = tk - 273.15  # Temperatura em Celsius

    cp = np.zeros(len_temp)
    cp_medio = np.zeros(len_temp)
    Q = np.zeros(len_temp)

    for i in range(0, len_temp):
        tcp = tk[i] / 1000

        # Correção do calor específico
        cp[i] = (A + (B * tcp) + (C * (tcp ** 2)) + (D * (tcp ** 3)) + (E / (tcp ** 2))) / mmol

        # Calor específico médio no intervalo considerado (cal/gºC)
        cp_medio[i] = (cp[0] + cp[i]) / 2

        # Energia Incidente no intervalo considerado (cal/cm²)
        # Q  = g * cal/gºC * ºC / cm^2
        Q[i] = (massa * cp_medio[i] * (tc[i] - tc[0]) / area)

    return Q


# def calc_by_ASTM(df: pd.DataFrame, column: str = 1):
#     A = 4.237312
#     B = 6.715751
#     C = -7.46962
#     D = 3.339491
#     E = 0.016389

#     mmol = 63.546                       # g/mol
#     massa = 18                          # g
#     diametro = 4                        # cm
#     area = np.pi * (diametro / 2) ** 2  # cm^2

#     if type(column) == int:
#         len_temp = len(df[df.columns[column]])
#         tk = np.array(df[df.columns[column]])    # Temperatura em Kelvin
#     elif type(column) == str:
#         len_temp = len(df[column])
#         tk = np.array(df[column])               # Temperatura em Kelvin
#     else:
#         raise Exception("Tipo do parâmetro 'columns' inválido.")

#     tc = tk - 273.15                    # Temperatura em Celsius

#     cp = np.zeros(len_temp)
#     cp_medio = np.zeros(len_temp)
#     Q = np.zeros(len_temp)

#     for i in range(0, len_temp):
#         tcp = tk[i] / 1000

#         # Correção do calor específico
#         cp[i] = (A + (B * tcp) + (C * (tcp ** 2)) +
#                  (D * (tcp ** 3)) + (E / (tcp ** 2))) / mmol

#         # Calor específico médio no intervalo considerado (cal/gºC)
#         cp_medio[i] = (cp[0] + cp[i]) / 2

#         # Energia Incidente no intervalo considerado (cal/cm²)
#         # Q  = g * cal/gºC * ºC / cm^2
#         Q[i] = (massa * cp_medio[i] * (tc[i] - tc[0]) / area)

#     df['EI'] = Q

#     return df

def calc_by_energia_interna(energia_interna: list):
    # Propriedadades do Cobre
    copper = dict()
    copper['densidade'] = 8978  # Densidade:       [ kg/m^3 ]
    copper['calor_esp'] = 381  # Calor específico: [ j/kg-k ]

    # Propriedades do Calorímetro
    calorimetro = dict()
    calorimetro['face_area'] = 12.5664  # mm^2 -> cm^2
    calorimetro['volume'] = 2010.6158 / 1e9  # mm^3 -> m^3
    calorimetro['massa'] = copper['densidade'] * calorimetro['volume']  # kg

    # Faz J/kg * kg
    # massa_x_energia_interna = list()
    # for i in energia_interna:
    #     massa_x_energia_interna.append(calorimetro['massa'] * i)
    massa_x_energia_interna = np.array(energia_interna) * calorimetro['massa']

    # Faz J / cm^2 e converte J -> cal
    ei = massa_x_energia_interna / calorimetro['face_area'] / 4.1868

    return ei
