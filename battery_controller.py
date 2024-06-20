from bokeh.io import curdoc
from bokeh.layouts import column,row
from bokeh.models import ColumnDataSource,TextInput,Button,DataTable,TableColumn,NumberFormatter, CustomJS, Div
from bokeh.plotting import figure
from datetime import datetime,timedelta,timezone
from urllib.request import urlopen
from xml.etree import ElementTree

class Bateria:
    def __init__(self, capacidade_maxima, eficiencia):
        self.capacidade_maxima = capacidade_maxima
        self.carga_atual = 0
        self.eficiencia = eficiencia
    
    def carregar(self, energia_ev):
        potencia_carregada = max(0, (self.capacidade_maxima - self.carga_atual) * self.eficiencia)
        self.carga_atual += potencia_carregada
    
    def descarregar(self, energia_ev):
        potencia_descarregada = max(0, energia_ev - 88)
        self.carga_atual -= potencia_descarregada
        self.carga_atual = max(0, self.carga_atual)
    
    def nivel_de_carga(self):
        return self.carga_atual


def get_dayahead_prices(api_key: str, area_code: str, start: datetime = None, end: datetime = None): 
    if not start:
        start = datetime.now().astimezone(timezone.utc)
    elif start.tzinfo and start.tzinfo != timezone.utc:
        start = start.astimezone(timezone.utc)
    if not end:
        end = start + timedelta(days=1)
    elif end.tzinfo and end.tzinfo != timezone.utc:
        end = end.astimezone(timezone.utc)

    fmt = '%Y%m%d%H00'
    url = f'https://web-api.tp.entsoe.eu/api?securityToken={api_key}&documentType=A44&in_Domain={area_code}' \
          f'&out_Domain={area_code}&periodStart={start.strftime(fmt)}&periodEnd={end.strftime(fmt)}'

    try:
        with urlopen(url) as response:
            if response.status != 200:
                raise Exception(f"HTTP status code: {response.status}")
            xml_str = response.read().decode()

        result = [0] * 24 
        for child in ElementTree.fromstring(xml_str):
            if child.tag.endswith("TimeSeries"):
                for ts_child in child:
                    if ts_child.tag.endswith("Period"):
                        for pe_child in ts_child:
                            if pe_child.tag.endswith("timeInterval"):
                                for ti_child in pe_child:
                                    if ti_child.tag.endswith("start"):
                                        start_time = datetime.strptime(ti_child.text, '%Y-%m-%dT%H:%MZ').replace(tzinfo=timezone.utc)
                            elif pe_child.tag.endswith("Point"):
                                for po_child in pe_child:
                                    if po_child.tag.endswith("position"):
                                        delta = int(po_child.text) - 1
                                        time_index = (start_time.hour + delta) % 24 
                                    elif po_child.tag.endswith("price.amount"):
                                        price = float(po_child.text)
                                        result[time_index] = price

        return result
    except Exception as e:
        print(f"Error fetching data: {e}")
        return [0] * 24 



api_key = "4513d294-67ee-43a2-9a3b-0c8335883d88" 
area_code = "10YPT-REN------W" 
precos_eletricidade = get_dayahead_prices(api_key, area_code)

tempo = list(range(24))

source_primeiras_seis_horas = ColumnDataSource(data=dict(x=[], y=[]))
source_horas_restantes = ColumnDataSource(data=dict(x=[], y=[]))
source_precos_eletricidade = ColumnDataSource(data=dict(horas=list(range(24)), precos=precos_eletricidade))
source_potencias = ColumnDataSource(data=dict(categoria=[], valor=[], color=[]))


plot_primeiras_seis_horas = figure(title="State of Charge da Bateria nas Primeiras 6 Horas", x_axis_label='Horas', y_axis_label='SOC (%)')
plot_primeiras_seis_horas.vbar(x='x', top='y', width=0.5, source=source_primeiras_seis_horas, color='green')

plot_horas_restantes = figure(title="Energia da Bateria nas Horas Restantes", y_axis_label='Energia (kWh)', x_range=(-1,1))
plot_horas_restantes.vbar(x='x', top='y', width=0.5, source=source_horas_restantes, color="blue")

plot_potencias = figure(title="Potências Asseguradas (Rede, Bateria, Total)", x_axis_label='Categoria', y_axis_label='Potência (kW)', x_range=['Rede', 'Bateria', 'Total'])
plot_potencias.vbar(x='categoria', top='valor', width=0.5, source=source_potencias, color='color')

columns = [
    TableColumn(field="horas", title="Hora"),
    TableColumn(field="precos", title="Preço (EUR/MWh)", formatter=NumberFormatter(format="0.00"))
]
data_table = DataTable(source=source_precos_eletricidade, columns=columns, width=400, height=280)

capacity_input = TextInput(value="50", title="Capacidade Máxima da Bateria (kWh):")
efficiency_input = TextInput(value="100", title="Eficiência da Bateria (%):")
num_ve_input = TextInput(value="0", title="Número de Veículos Elétricos:")
update_button = Button(label="Atualizar Gráficos")


error_div = Div(text='', style={'color': 'red'})

def show_alert(message):
    error_div.text = message

def update_plots():
    try:
        capacidade_maxima = int(capacity_input.value)
        eficiencia = int(efficiency_input.value) / 100
        num_ve = int(num_ve_input.value)
        energia_ev = num_ve * 11  
        bateria = Bateria(capacidade_maxima, eficiencia)
        capacidade_infraestrutura = 88;
        num_ve_infmax=8;
        
        if not (0 <= capacidade_maxima <= 50):
            show_alert("Capacidade Máxima deve estar entre 0 e 50 kWh.")
            return
        if not (0 <= eficiencia <= 1):
            show_alert("Eficiência deve estar entre 0% e 100%.")
            return
        if not (0 <= num_ve <= 12):
            show_alert("Número de Veículos Elétricos deve estar entre 0 e 12.")
            return
        
        cargas_bateria_primeiras_seis_horas = []
        for i in range(6):
            preco_atual = precos_eletricidade[i]
            if preco_atual == min(precos_eletricidade[:6]):
                bateria.carregar(capacidade_maxima)
            cargas_bateria_primeiras_seis_horas.append(bateria.nivel_de_carga())
       
        soc = (bateria.carga_atual / bateria.capacidade_maxima) * 100
        
        if energia_ev <= capacidade_infraestrutura and bateria.carga_atual < bateria.capacidade_maxima and bateria.carga_atual + energia_ev <= capacidade_infraestrutura and num_ve<=num_ve_infmax:
            bateria.carregar(energia_ev)
        elif energia_ev > capacidade_infraestrutura and soc > 20 and num_ve > num_ve_infmax:
            bateria.descarregar(energia_ev)
        
        carga_bateria_horas_restantes = bateria.nivel_de_carga()
        
        source_primeiras_seis_horas.data = dict(x=list(range(6)), y=[c / capacidade_maxima * 100 for c in cargas_bateria_primeiras_seis_horas])
        source_horas_restantes.data = dict(x=[0], y=[carga_bateria_horas_restantes])
        
        potencia_rede = min(capacidade_infraestrutura, energia_ev)
        potencia_bateria = max(0, energia_ev - capacidade_infraestrutura) if energia_ev > capacidade_infraestrutura else 0
        potencia_total = potencia_rede + potencia_bateria

        source_potencias.data = dict(
            categoria=['Rede', 'Bateria', 'Total'], 
            valor=[potencia_rede, potencia_bateria, potencia_total],
            color=['red', 'blue', 'green']
        )
        show_alert("") 
    
    except ValueError as e:
        show_alert(f"Erro de valor: {e}")

update_button.on_click(update_plots)

layout = column(
    capacity_input, 
    efficiency_input, 
    num_ve_input, 
    update_button, 
    error_div,
    row(plot_primeiras_seis_horas, plot_horas_restantes, plot_potencias), 
    data_table
)

curdoc().add_root(layout)
