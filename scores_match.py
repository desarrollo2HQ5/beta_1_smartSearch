import numpy as np
import pandas as pd
from datetime import datetime
import seaborn as sns
import urllib3
import json

hv = pd.DataFrame(data=None)

class SmartSearch:
    def __init__(self):
        pass

    @staticmethod
    def process_database(ruta="C:/Users/CO-149/Downloads/Hojas de Vida Creadas (3).csv",
                         ruta_out="c:/Users/CO-149/Downloads/out.csv"):
        hv = pd.read_csv(ruta)

        def normalize(s, replacements):
            for a, b in replacements:
                s = s.replace(a, b).replace(a.lower(), b.lower()).lower()
            return s

        column_names = []
        for x in hv.columns:
            y = normalize(x, (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), (" ", "_"), ("ñ", "n"),
                              ("(", ""), (")", ""), (",", ""), (".", "")))
            column_names.append(y)

        hv.columns = column_names

        def predecir_genero(first_name):
            tablaTemporal = hv[(hv["primer_nombre"] == first_name) & (hv["genero_de_nacimiento"] != "NaN")]
            count = 0
            http = urllib3.PoolManager()
            for row in tablaTemporal.index:
                if tablaTemporal["genero_de_nacimiento"][row] == "MASCULINO":
                    count += 1
                else:
                    count -= 1
            if count == 0:
                url = "https://api.genderize.io/?name=" + first_name
                gender = json.loads(http.request('GET', url).data.decode('utf-8')).get("gender")
                if gender == "female":
                    response = "FEMENINO"
                elif gender == "male":
                    response = "MASCULINO"
                else:
                    response = "NaN"
            elif count > 0:
                response = "MASCULINO"
            else:
                response = "FEMENINO"
            return response

        table = hv[hv.genero_de_nacimiento.isnull()]
        for x in table.index:
            hv["genero_de_nacimiento"][x] = predecir_genero(str(hv["primer_nombre"][x]))

        hv["genero_femenino"] = np.where(hv["genero_de_nacimiento"] == "FEMENINO", 1, 0)

        hv["num_cargos"] = 0
        for index in range(0, len(hv)):
            if type(hv["historia_laboral"][index]) == str:
                hv["num_cargos"][index] = hv["historia_laboral"][index].count("| ,") + 1
            else:
                hv["num_cargos"][index] = 0

        # Contabilizamos la catidad de trabajos que ha tenido hasta la fecha
        Experiencia = "historia_laboral"
        var_ref = "num_cargos"
        hv[[Experiencia, var_ref]].describe()
        sns.histplot(hv["num_cargos"])

        def string_to_list(cargo_string) -> object:
            # Convierne en matriz la xp donde cada vector es un registro de xp
            try:
                cargos = cargo_string.split("|| ,")
                listaCargos = []
                for cargo in cargos:
                    listaCargos.append(cargo.split(" || "))
            except:
                listaCargos = []
            return listaCargos

        hv["lista_cargos"] = ""
        for x in hv.index:
            if hv["num_cargos"][x] == 0:
                hv["lista_cargos"][x] = ""
            else:
                hv["lista_cargos"][x] = string_to_list(hv["historia_laboral"][x])

        hv["lista_estudios"] = ""
        for x in hv.index:
            try:
                hv["lista_estudios"][x] = string_to_list(hv["historia_escolar"][x])
            except:
                hv["lista_estudios"][x] = ""

        def tranfor_to_date(date):
            # Convierto la data en fecha y reordeno los datos del año
            dateList = date.split("/")
            day = int(dateList[0])
            mount = int(dateList[1])
            year_str = dateList[2].strip()
            if (year_str[:2] != "20") | (len(year_str) != 4):
                if year_str[2] != ('0', '1', '2'):
                    new_year = "20" + year_str[2:]
                else:
                    new_year = "20" + year_str[3] + year_str[2]
                year = int(new_year)
            else:
                year = int(year_str)
            return datetime(year, mount, day)

        def calculate_experience(cargo_list, position):
            # Devuelve la xp en años
            try:
                xp = 0
                for dataCargo in cargo_list:
                    if dataCargo[2] != '':
                        if dataCargo[3] == '':
                            xp_days = abs((hv["added_time"][position] - tranfor_to_date(dataCargo[2])).days)
                        else:
                            xp_days = abs((tranfor_to_date(dataCargo[3]) - tranfor_to_date(dataCargo[2])).days)
                    else:
                        xp_days = 0
                    xp = xp + xp_days  # type: ignore
                totalExperiencia = xp / 365
            except Exception:
                totalExperiencia = -1
            return totalExperiencia

        def info_experience(cargo_list, position=6):
            ''' Concatena educación, experiencia, cursos adicionales en un solo bloque de texto, elimina caracteres especiales'''
            funciones = ""
            try:
                for cargo in cargo_list:
                    if cargo[6] != "":
                        funciones = funciones + " " + normalize(cargo[position], (("á", "a"), ("é", "e"), ("í", "i"),
                                                                                  ("ó", "o"), ("ú", "u"), (" ", " "),
                                                                                  ("(", ""), (")", ""),
                                                                                  (",", ""), (".", ""), (";", ""),
                                                                                  (":", ""), ("  ", " ")
                                                                                  )
                                                                )
            except Exception:
                funciones = ""

            return funciones

        hv["xp"] = 0
        hv["info_candidato"] = ""
        for x in range(0, len(hv)):
            if hv["num_cargos"][x] > 0:
                hv["info_candidato"][x] = info_experience(hv["lista_cargos"][x]) + " " + info_experience(
                    hv["lista_estudios"][x], position=3)
                hv["xp"][x] = calculate_experience(hv["lista_cargos"][x], x)
            else:
                hv["xp"][x] = 0

        hv["lista_palabras"] = ""
        for x in hv.index:
            try:
                hv["lista_palabras"][x] = hv["info_candidato"][x].split(" ")
            except:
                hv["lista_palabras"][x] = ""

        for x in hv.index:
            unique_sweets = []
            [unique_sweets.append(sweet) for sweet in hv["lista_palabras"][x] if sweet not in unique_sweets]
            hv["lista_palabras"][x] = unique_sweets

        hv["num_nivel_educativo"] = np.where(
            (hv["nivel_educativo"] == "NINGUNO"),
            0,
            np.where(
                (hv["nivel_educativo"] == "BASICA PRIMARIA"),
                1,
                np.where(
                    (hv["nivel_educativo"] == "MEDIA ACADEMICA (BACHILLER)"),
                    2,
                    np.where(
                        (hv["nivel_educativo"] == "TECNICA PROFESIONAL"),
                        3,
                        np.where(
                            (hv["nivel_educativo"] == "TECNOLOGICA"),
                            4, np.where(
                                (hv["nivel_educativo"] == "PROFESIONAL"),
                                5,
                                np.where(
                                    (hv["nivel_educativo"] == "POSTGRADO"),
                                    6,
                                    0
                                )
                            )
                        )
                    )
                )
            )
        )

        # Tiempo que una persona dura en promedio por cada cargo
        hv["estabilidad_laboral"] = 0
        for x in hv.index:
            try:
                hv["estabilidad_laboral"][x] = (hv["xp"][x] / hv["num_cargos"][x])
            except Exception as e:
                hv["estabilidad_laboral"][x] = 0
            if hv["estabilidad_laboral"][x] < 0:
                hv["estabilidad_laboral"][x] = 0

        hv["estabilidad_laboral"] = np.where(
            hv["estabilidad_laboral"].isnull(),
            0,
            np.where(
                hv["estabilidad_laboral"] > 20,
                20,
                hv["estabilidad_laboral"]
            )
        )

        hv.to_csv(path_or_buf=ruta_out)

    @staticmethod
    def smart_search(age_minima=18, age_maxima=54, gender=2, palabras_clave=None, nivel_educativo=0,
                     tiempo_experiencia=0, ruta="c:/Users/CO-149/Downloads/out.csv", w_genero=0.06, w_edad=0.06,
                     w_educacion=0.2, w_experiencia=0.15, w_match=0.5, w_ciudad=0.03, ciudad=""):
        """ Función que busca y puntua cada uno de los criterios de busqueda especificados """
        if palabras_clave is None:
            palabras_clave = []
        base = pd.read_csv(ruta)
        lista_puntaje = []
        for x in base.index:
            score = 0
            lista_match = []

            """Ciudad"""
            city = base["ciudad"][x]
            if city == ciudad:
                score = score + w_ciudad

            """Genero 0.0625"""
            if gender != 2:
                if base["genero_femenino"][x] == gender:
                    score = score + w_genero
                    lista_match.append("genero")
            else:
                score = score + w_genero

            """rango de edad  0.0625 """
            try:
                edad = int(base["edad"][x])
                if edad >= age_minima & edad <= age_maxima:
                    score = score + w_edad
                    lista_match.append("edad")
            except Exception:
                score = score + 0

            """nivel educativo 0.125"""
            niv_educativo = base["num_nivel_educativo"][x]
            if niv_educativo == nivel_educativo:
                score = score + w_educacion
                lista_match.append("educacion")
            elif niv_educativo >= nivel_educativo:
                score = score + (w_educacion / 2)

            """Experiencia 0.125"""
            experiencia = base["experiencia"][x]
            if experiencia >= tiempo_experiencia:
                score = score + w_experiencia
                lista_match.append("experiencia")

            """Match etiquetas 0.5"""
            num_palabras = len(palabras_clave)
            if num_palabras != 0:
                texto = base["lista_palabras"][x]
                for y in palabras_clave:
                    if texto.__contains__(y):
                        lista_match.append(y)
                score = score + ((len(lista_match) / num_palabras) * w_match)
            else:
                score = score + 0.5

            lista_puntaje.append([score, lista_match])

        df = pd.DataFrame(lista_puntaje, columns=["score", "lista_match"])
        hv_final = pd.concat([base, df], axis=1)
        return hv_final


#if __name__ == '__main__':
   # start_time = datetime.now()
   # objeto = SmartSearch()
   # SmartSearch.process_database()
   # deltaTime = datetime.now() - start_time
   # print(deltaTime)

    # dataframe = SmartSearch.smart_search(gender=0,
    #                                      palabras_clave=["auxiliar", "bodega", "descargue"],
    #                                      nivel_educativo=0)

    # data2 = dataframe[["no_identificacion", "score", "lista_match"]]
    # data2.to_excel("c:/Users/CO-149/Downloads/score.xlsx")
    # deltaTime = datetime.now() - start_time
    # print(deltaTime)

#
