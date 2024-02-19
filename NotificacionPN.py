# -*- coding: utf-8 -*-
"""
Created on Thu Mar  9 12:32:23 2023

@author: jcgarciam
"""

import pandas as pd
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import six
from fpdf import FPDF

Tiempo_Total = datetime.now()

Current_Date = datetime.today().date()

print('La fecha del archivo de es: ', Current_Date)

Current_Date = Current_Date.strftime('%Y')+Current_Date.strftime('%m')+ Current_Date.strftime('%d')


path_int = r'D:\DATOS\Users\jcgarciam\OneDrive - AXA Colpatria Seguros\Documentos\Informes\Notificaction Persona Natural\Input'
path_out = r'D:\DATOS\Users\jcgarciam\OneDrive - AXA Colpatria Seguros\Documentos\Informes\Notificaction Persona Natural\Output'

#%%

op = pd.read_csv(path_int + '\OP.txt', header = 0, sep = '|', encoding = 'ANSI',
                 usecols = ['FEC_ESTADO','ESTADO','NRO_OP'])

soat = pd.read_csv(path_int + '\SOAT.txt', header = 0, sep = '|', encoding = 'ANSI',
                   usecols = ['nro_comprob','nro_op','SLxP','txt_cobertura',
                              'nro_doc_benef','nro_stro_SIS','nom_concepto',
                              'txt_cheque_a_nom','marca_anul'])

#%%
comparativo = pd.read_csv(path_int + '/'+ Current_Date +' Comparativo Reserva pendiente y En proceso.csv', 
                           header = 0, sep = ';', encoding = 'ANSI', 
                           usecols = ['Reclamacion','Cedula Accidentado','Nombres Accidentado'])

#%%

def CambioFormato(df, a = 'a'):
    df[a] = df[a].astype(str).str.strip().str.strip('\x02')
    df[a] = np.where(df[a].str[-2::] == '.0', df[a].str[0:-2], df[a])
    df[a] = np.where(df[a] == 'nan', np.nan, df[a])
    return df[a]

#%%

op2 = op.copy()
op2 = op2[op2['ESTADO'].str.upper() == 'PAGADA']
op2['FEC_ESTADO'] = pd.to_datetime(op2['FEC_ESTADO'],dayfirst = True)

fecha_inicial = datetime.strptime(input('Ingrese la fecha inicial (yyyy-mm-dd): '), "%Y-%m-%d")
fecha_final = datetime.strptime(input('Ingrese la fecha final (yyyy-mm-dd): '), "%Y-%m-%d")

op2 = op2[op2['FEC_ESTADO'].between(fecha_inicial, fecha_final) == True]
#%%
soat2 = soat.copy()

soat2 = soat2[soat2['nom_concepto'].str.title() == 'Indemnizacion']
soat2 = soat2[soat2['marca_anul'].str.upper() == 'NO']
soat2 = soat2[soat2['nro_op'] != '0']
soat2 = soat2[soat2['txt_cheque_a_nom'].str.upper().str.contains('BANCO AGRARIO') == False]
soat2 = soat2[soat2['txt_cobertura'].str.upper().isin(['INCAPACIDAD PERMANENTE','MUERTE Y GASTOS  FUNERARIOS']) == True]


op2['NRO_OP'] = CambioFormato(op2, a = 'NRO_OP')

soat2['nro_op'] = CambioFormato(soat2, a = 'nro_op')

soat2 = soat2.merge(op2, how = 'inner', left_on = 'nro_op', right_on = 'NRO_OP', validate = 'many_to_one')

soat2.drop(columns = ['nro_op'], inplace = True)

soat2['nro_stro_SIS'] = CambioFormato(soat2, a = 'nro_stro_SIS')

comparativo['Reclamacion'] = CambioFormato(comparativo, a = 'Reclamacion')

comparativo.drop_duplicates('Reclamacion', inplace = True)

soat2 = soat2.merge(comparativo, how = 'left', left_on = 'nro_stro_SIS', right_on = 'Reclamacion')

soat2.drop(columns = 'Reclamacion', inplace = True)
#%%
soat2['nro_doc_benef'] = CambioFormato(soat2, a = 'nro_doc_benef')
soat2 = soat2.rename(columns = {'nro_doc_benef':'ID Apoderado','nro_stro_SIS':'N° Reclamación',
                                'NRO_OP':'Orden de Pago','txt_cobertura':'Amparo/Cobertura',
                                'Cedula Accidentado':'Id Lesionado','FEC_ESTADO':'Fecha_Pago',
                                'SLxP':'Valor Girado','Nombres Accidentado':'Nombre Lesionado'})
print('\n Existen ', len(soat2['ID Apoderado'].unique()), ' ID Apoderados diferentes con Pagos')
#%%
soat2['Nombre Lesionado'] = soat2['Nombre Lesionado'].str.title()
soat2 = soat2[['N° Reclamación','Orden de Pago','Amparo/Cobertura','Id Lesionado','Nombre Lesionado','ID Apoderado','Fecha_Pago','Valor Girado']]
soat2['Valor Girado'] = '$ ' + soat2['Valor Girado'].map('{:,.1f}'.format)
soat2['Id Lesionado'] = CambioFormato(soat2, a = 'Id Lesionado')
soat2['Fecha_Pago'] = soat2['Fecha_Pago'].dt.strftime('%d/%m/%Y')

#%%

def render_mpl_table(data, col_width= 0.5, row_height=0.625, font_size=10,
                     header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='black',
                     bbox=[0, 0, 1, 1], header_columns=0,
                     ax=None, **kwargs):
    if ax is None:
        size = (np.array(data.shape[::-1]) + np.array([1, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        ax.axis('off')

    mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)

    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(font_size)
    mpl_table.auto_set_column_width([0,1,2,3,4,5,6,7])

    for k, cell in six.iteritems(mpl_table._cells):
        cell.set_edgecolor(edge_color)
        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight='bold', color='w')
            cell.set_facecolor(header_color)
        else:
            cell.set_facecolor(row_colors[k[0]%len(row_colors) ])
    return ax, fig

#%%
from pandas.plotting import table
import matplotlib.pyplot as plt


c = 1
b = len(soat2['ID Apoderado'].unique())

for i in soat2['ID Apoderado'].unique():
    d = str(c) + '.'
    print(d, ' filtranddo información para el ID Apoderado: ',i)
    df = soat2[soat2['ID Apoderado'].astype(str) == str(i)]    
    ax, fig = render_mpl_table(df, header_columns=0, col_width=2.0)
    fig.savefig('./' + i + '.png')
    pdf = FPDF(orientation = 'L')
    pdf.add_page()
    pdf.set_font('arial', '', 10)
    pdf.cell(60, ln = 2)
    pdf.cell(0, 0, '          AXA COLPATRIA SEGUROS SA',  0, 2, 'L')
    pdf.cell(0, 10, '          860 002 184 - 9', 0, 2, 'L')
    pdf.cell(0, 10, '          NOTIFICACIÓN DE PAGOS PERSONA NATURAL', 0, 2, 'L')
    concept = '          Soportes de pago por concepto de indemnizaciones correspondientes desde la fecha ' + fecha_inicial.strftime('%d/%m/%Y') + ' hasta la fecha ' + fecha_final.strftime('%d/%m/%Y') + ' Ramo SOAT'
    pdf.cell(0, 10, concept, 0, 2, 'L')

    pdf.cell(90, 10, ' ', 0, 2, 'C')
    pdf.cell(-55)


    pdf.image('./' + i + '.png', x = 0, y = 50, w = 300, type = 'png')
    pdf.image(path_int + '/axa_image.png', x = 200, y = 140, type = 'png', w = 70)

    pdf.cell(0,120, ln = 2)
    pdf.cell(0, 5, 'GESTION DE SINIESTROS ARL SALUD SOAT          ', 0, 1, 'R')
    pdf.cell(0, 5, 'PAGOS TÉCNICOS AXA COLPATRIA SEGUROS S.A          ', 0, 1, 'R')
    pdf.cell(0, 5, 'JKDC         ', 0, 1, 'R')

    pdf.output(path_out + '/' + i + '.pdf', 'F')   
    print('    Guardando información para el ID Apoderado: ',i)
    #df.to_excel(path_out + '/' + str(i) + '.xlsx', index = False)
    print('    Información guardada para el ID Apoderado: ',i, '\n')
    b -= 1
    print(' Quedan ',b, ' archivos por guardar \n')
    c += 1
    
#%% 
nits = {'ID Apoderado':list(soat2['ID Apoderado'].unique())}
nits = pd.DataFrame(nits)
nits.to_excel(path_out + '/ID Apoderados.xlsx', index = False)
    
    
print('fin del proceso')    
print(len(soat2['ID Apoderado'].unique()), ' ID Apoderados diferentes guardados')
print("Tiempo final del Proceso: " , datetime.now()-Tiempo_Total)










