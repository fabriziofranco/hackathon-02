import csv, json

departamentos ={}
provincias={}
distritos=[]
contador_departamentos=1
contador_provincias=1
lista=[]
with open('geodir-ubigeo-inei.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count != 0:
            if row[2] not in departamentos:
                departamentos[row[2]]= contador_departamentos
                contador_departamentos+=1
            if row[1] not in provincias:
                provincias[row[1]]=contador_provincias
                contador_provincias+=1

            distritos.append({"model": "agricultores.district",
             "pk": len(lista)+1,
             "fields":
                 {
                     "name": row[0],
                     "department": departamentos[row[2]],
                     "region":provincias[row[1]]
                 }
             })
            lista.append(row[0])
        line_count += 1

with open('../agricultores/fixtures/distritos.json', 'w') as fp:
    json.dump(distritos, fp,indent=4)
