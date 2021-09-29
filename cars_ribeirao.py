import geopandas as gpd
import matplotlib.pyplot as plt
import dash
from dash import html
import dash_bootstrap_components as dbc
from io import BytesIO
import base64
from scipy.sparse.csgraph import connected_components


def fig_to_uri(in_fig, close_all=True, **save_args):
    out_img = BytesIO()
    in_fig.savefig(out_img, format='png', **save_args)
    if close_all:
        in_fig.clf()
        plt.close('all')
    out_img.seek(0)  # rewind file
    encoded = base64.b64encode(out_img.read()).decode("ascii").replace("\n", "")
    return "data:image/png;base64,{}".format(encoded)


sp = gpd.read_file('mapas/sp/SP_Municipios_2020.shp')

rp = sp.query("NM_MUN == 'Ribeirão Preto'")

gs_rp = gpd.GeoSeries(rp['geometry'])
crs_rp = gs_rp.to_crs(epsg=3857)

#CALCULANDO O KM² DE RIBEIRAO PRETO
km2_rp = crs_rp.area/10**6

area_car_rp = gpd.read_file('cars/sp/ribeirao_preto/area_imovel/AREA_IMOVEL.shp')

# INDICANDO AS SOBREPOSICOES
index_sobreposicao = area_car_rp['geometry'].apply(lambda x: area_car_rp['geometry'].overlaps(x)).values.astype(int)

# CONECTANDO OS COMPONENTES
n, ids = connected_components(index_sobreposicao)

# AGREGACAO COM DISSOLVE
df = gpd.GeoDataFrame({'geometry': area_car_rp['geometry'], 'group': ids})
area_car_sem_sobreposicao = df.dissolve(by='group')

area_car_sem_sobreposicao['KM2'] = gpd.GeoSeries(area_car_sem_sobreposicao['geometry']).to_crs(epsg=3857).area/10**6

plt.figure(1)
fig_area_car, ax_rp = plt.subplots(figsize  = (5, 4)) 
rp_plot = rp.plot(ax=ax_rp)
ax_rp.spines['top'].set_visible(False)
ax_rp.spines['left'].set_visible(False)
ax_rp.spines['right'].set_visible(False)
ax_rp.spines['bottom'].set_visible(False)
ax_rp.set_yticklabels([])
ax_rp.set_xticklabels([])
ax_rp.set_xticks([])
ax_rp.set_yticks([])

intercessao = gpd.overlay(area_car_sem_sobreposicao, rp, how='intersection')
intercessao['LABEL'] = 'Cadastro Ambiental Rural'
gs_intercessao = gpd.GeoSeries(intercessao['geometry'])
crs_intercessao = gs_intercessao.to_crs(epsg=3857)

#CALCULANDO O KM² DA INTERCESSAO ENTRE OS CARS E RIBEIRAO PRETO
km2_intercessao = crs_intercessao.area/10**6
km2_intercessao = km2_intercessao.sum()

plt.figure(2)
fig_intercessao, ax_inter = plt.subplots(figsize  = (5, 4))
intercessao.plot(ax=ax_inter, color='red')
ax_inter.spines['top'].set_visible(False)
ax_inter.spines['left'].set_visible(False)
ax_inter.spines['right'].set_visible(False)
ax_inter.spines['bottom'].set_visible(False)
ax_inter.set_yticklabels([])
ax_inter.set_xticklabels([])
ax_inter.set_xticks([])
ax_inter.set_yticks([])

plt.figure(3)
fig_rp_intercessao, ax_rp_inter = plt.subplots(figsize  = (8, 8))
rp_plot = rp.plot(ax=ax_rp_inter)
plot_intercessao = intercessao.plot(ax=rp_plot, color='red')
ax_rp_inter.spines['top'].set_visible(False)
ax_rp_inter.spines['left'].set_visible(False)
ax_rp_inter.spines['right'].set_visible(False)
ax_rp_inter.spines['bottom'].set_visible(False)
ax_rp_inter.set_yticklabels([])
ax_rp_inter.set_xticklabels([])
ax_rp_inter.set_xticks([])
ax_rp_inter.set_yticks([])

area_car_src = fig_to_uri(fig_area_car)
intercessao_src = fig_to_uri(fig_intercessao)
intercessao_rp_src = fig_to_uri(fig_rp_intercessao)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.GRID])

app.layout = html.Div([
    html.H1(children="Cadastro Ambiental Rural - Ribeirão Preto", style={"text-align": "center"}),
    html.P(
        children="Análise das áreas de Cadastro Ambiental Rural"
        " da cidade de Ribeirão Preto", 
        style={"text-align": "center", "margin-bottom": "100px"}
    ),
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H4(
                    children="Mapa da região de Ribeirão Preto",
                    style={"text-align": "center"}
                ),
                html.P(
                    children="Aréa em Km²: "+str(round(km2_rp.iloc[0], 2)), 
                    style={"text-align": "center"}
                ),
                html.Img(src=area_car_src, style={"display": "block", "margin": "0 auto"})
            ]),
        ], style={"margin-left":"20px", "margin-right":"10px", "border": "1px solid"}),
        dbc.Col([
            html.Div([
                html.H4(
                    children="Mapa dos Cadastros Ambientais Rurais de Ribeirão Preto",
                    style={"text-align": "center"}
                ),
                html.P(
                    children="Aréa em Km²: "+str(round(km2_intercessao, 2)), 
                    style={"text-align": "center"}
                ),
                html.Img(src=intercessao_src, style={"display": "block", "margin": "0 auto"})
            ]),
        ], style={"margin-left":"10px", "margin-right":"20px", "border": "1px solid"})
    ], style={"margin-bottom": "100px"}),
    
    html.Div([
        html.H4(
            children="Mapa da Intercessão entre os Cadastros Ambientais Rurais e Ribeirão Preto",
            style={"text-align": "center"}
        ),
        html.Img(src=intercessao_rp_src, style={"display": "block", "margin": "0 auto"})
    ], style={"margin-left":"5px", "margin-right":"5px" , "border": "1px solid"}),

])

if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
