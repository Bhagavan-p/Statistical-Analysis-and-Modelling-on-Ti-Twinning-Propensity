from flask import Flask, render_template, request, jsonify
import pickle
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
lr_frac_5p = pickle.load(open('lr_frac_5p.pkl', 'rb'))
lr_frac_10p = pickle.load(open('lr_frac_10p.pkl', 'rb'))
lr_at_5p = pickle.load(open('lr_at_5p.pkl', 'rb'))
lr_at_10p = pickle.load(open('lr_at_10p.pkl', 'rb'))
lr1_tt_5p = pickle.load(open('lr1_tt_5p.pkl', 'rb'))
lr2_tt_5p = pickle.load(open('lr2_tt_5p.pkl', 'rb'))
lr1_tt_10p = pickle.load(open('lr1_tt_10p.pkl', 'rb'))
lr2_tt_10p = pickle.load(open('lr2_tt_10p.pkl', 'rb'))

def overlapping_function(x,xmin, xmax):
    v = (2*(x-xmin) / (xmax - xmin)) - 1
    return 1 / (1 + np.exp(4*v / (1- v**2)))


interpolation_range = np.arange(1, 16)
def interpolation(a5, a10):
  l = []
  for i in range(1, 16):
    l.append(a5 + (a10 - a5) * ((i-5) / 5))
  return l

c_f5 = lr_frac_5p.intercept_
m_f5 = lr_frac_5p.coef_[0]
c_f10 = lr_frac_10p.intercept_
m_f10 = lr_frac_10p.coef_[0]

list_fm = interpolation(m_f5, m_f10)
list_fc = interpolation(c_f5, c_f10)

frac_ = pd.DataFrame()
frac_['strain'] = np.arange(1, 16)
frac_['a1'] = np.array(list_fm).reshape(-1,1)
frac_['a0'] = np.array(list_fc).reshape(-1,1)

c_n5 = lr_at_5p.intercept_
m_n5 = lr_at_5p.coef_[0]
c_n10 = lr_at_10p.intercept_
m_n10 = lr_at_10p.coef_[0]
list_nm = interpolation(m_n5, m_n10)
list_nc = interpolation(c_n5, c_n10)

no_twins_ = pd.DataFrame()
no_twins_['strain'] = np.arange(1, 16)
no_twins_['a1'] = np.array(list_nm).reshape(-1,1)
no_twins_['a0'] = np.array(list_nc).reshape(-1,1)

#Area (0 - 400)
c_t5 = lr1_tt_5p.intercept_
m_t5 = lr1_tt_5p.coef_[0]
c_t10 = lr1_tt_10p.intercept_
m_t10 = lr1_tt_10p.coef_[0]
list_tm = interpolation(m_t5, m_t10)
list_tc = interpolation(c_t5, c_t10)

twin_thk1_ = pd.DataFrame()
twin_thk1_['strain'] = np.arange(1, 16)
twin_thk1_['a1'] = np.array(list_tm).reshape(-1,1)
twin_thk1_['a0'] = np.array(list_tc).reshape(-1,1)

#Area (400 - 600)
c_t5 = lr2_tt_5p.intercept_
m_t5 = lr2_tt_5p.coef_[0]
c_t10 = lr2_tt_10p.intercept_
m_t10 = lr2_tt_10p.coef_[0]
list_tm = interpolation(m_t5, m_t10)
list_tc = interpolation(c_t5, c_t10)

twin_thk2_ = pd.DataFrame()
twin_thk2_['strain'] = np.arange(1, 16)
twin_thk2_['a1'] = np.array(list_tm).reshape(-1,1)
twin_thk2_['a0'] = np.array(list_tc).reshape(-1,1)

def calculate_grain(area, StrainLevel):
    StrainLevel = int(StrainLevel[0])
    fraction_twins = frac_[frac_['strain'] == StrainLevel]['a1'] * area + frac_[frac_['strain'] == StrainLevel]['a0']
    if fraction_twins.values[0] < 0:
        fraction_twins.values[0] = 0
    if fraction_twins.values[0] > 1:
        fraction_twins.values[0] = 1 
    average_no_of_twins = no_twins_[no_twins_['strain'] == StrainLevel]['a1'] * area + no_twins_[no_twins_['strain'] == StrainLevel]['a0']
    twin_thk11 = []
    twin_thk22 = []
    if area <= 390 :
        average_twins_thickness = twin_thk1_[twin_thk1_['strain'] == StrainLevel]['a1'] * area + twin_thk1_[twin_thk1_['strain'] == StrainLevel]['a0']
    elif area > 390 and area <= 410:
        twin_thk11 = twin_thk1_[twin_thk1_['strain'] == StrainLevel]['a1'] * area + twin_thk1_[twin_thk1_['strain'] == StrainLevel]['a0']
        twin_thk22 = twin_thk2_[twin_thk2_['strain'] == StrainLevel]['a1'] * area + twin_thk2_[twin_thk2_['strain'] == StrainLevel]['a0']
        weight_1 = overlapping_function(area, 390, 410)
        weight_2 = 1 - weight_1
        average_twins_thickness =  weight_1 * twin_thk11 + weight_2 * twin_thk22
    elif area > 410 and area <= 600 :
        average_twins_thickness = twin_thk2_[twin_thk2_['strain'] == StrainLevel]['a1'] * area + twin_thk2_[twin_thk2_['strain'] == StrainLevel]['a0']
    if average_twins_thickness.values[0] < 0:
        average_twins_thickness.values[0] = 0
    return {
        'fraction_twins': str(fraction_twins.values[0]),
        'average_no_of_twins': str(average_no_of_twins.values[0]),
        'average_twins_thickness': str(average_twins_thickness.values[0])
    }

app = Flask(__name__)

# Create a function to render the HTML template with the grain calculation form
def render_grain_form(output=""):
    return render_template('gui.html', output=output)

# Route for rendering the HTML page with the grain calculation form
@app.route('/', methods=['GET', 'POST'])
def generate():
    output = {}
    if request.method == 'POST':
        data = request.get_json()  # Retrieve JSON data
        area = data['area']  # Extract 'area' from JSON
        StrainLevel = data['StrainLevel']  # Extract 'StrainLevel' from JSON
        # Calculate grain parameters
        output = calculate_grain(float(area), StrainLevel)
        return jsonify(output)
    return render_grain_form(output=output)

# This code snippet starts the Flask application if the script is being run directly as the main program, running on the IP address '0.0.0.0' and port number 8080.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)