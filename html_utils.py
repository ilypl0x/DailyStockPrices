import os
import html as html_lib
import inspect
import socket as socket_lib
import pandas as pd
import numpy as np

def df_to_styled_html(df, row_style_function, header=''):
    html = header

    # Change to axis = 1 for Rows; Axis = 0 for Columns
    html += df.style.apply(row_style_function, axis=None) \
        .set_table_attributes('border="1"') \
        .hide_index() \
        .render()

    html += '<br/>'

    return html

def finalize_html_report(title,body):

# Takes in a variable for title, and body (in html format already) which it then 
# inserts into the below structure 

    header= '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <style>
        table {
            border-collapse: collapse;
            border-color: black;
            font-size: 14px;
        }

        h2 {
            background-color: #4783DF;
            color: white;
        }

        .header {
            background-color: #4783DF;
            color: white;
            font-size: 20px;
            padding: 2px;
        }

        th {
            padding: 2px;
            background-color: #4783DF;
            color: white;
            text-align: left;
        }

        td {
            padding: 2px;
        }
        </style>
        </head>
        '''    
    body_open = '<body><h2>{0}</h2><p>'.format(title)
    frame = inspect.stack()[-1]
    module = inspect.getmodule(frame[0])
    body_close = '<hr/>{socket}: {script_path}</p></body>'.format(socket=socket_lib.gethostname(),script_path=os.path.realpath(module.__file__))
    footer = '</html>'
    html = ''.join([header,body_open,body,body_close,footer])   
    return html

def default_html_layout(msg,escape_message=False):

    if escape_message:
        msg = html_lib.escape(msg)
    html = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <style>
        </style>
        </head>
        <body>
        {message}
        '''.format(message=msg)

        #Add script location
    frame = inspect.stack()[-1]
    module = inspect.getmodule(frame[0])
    html += '<hr/>{socket}: {script_path}'.format(socket=socket_lib.gethostname(),script_path=os.path.realpath(module.__file__))
    html += '</body></html>'
    return html

class ColorDFRows(object):
    def __init__(self,df):
        self.df = df

    def create_series(self, row_index, bg_color ='white'):
        colors = {
            'green': '#89D86B',
            'red': ' #D86B8E',
            'white': '#FFFFFF' 
        }
        #obviously, change to background-color if you want to apply to the enitre row instead of just font color change
        # return pd.Series('background-color: %s' % (colors[bg_color]), row_index)
        return pd.Series('color: %s' % (colors[bg_color]), row_index)

    def getColor(self):

        def row_style(row):
            print(row)
            if row['% Chg'] > 0:
                return self.create_series(row.index, bg_color='green')
            else:
                return self.create_series(row.index, bg_color='red')

        def color_negative_red(x):
            c1 = 'color: red'
            c2 = 'color: green'

            cols = x.select_dtypes(np.number).columns
            df1 = pd.DataFrame('',index=x.index, columns=x.columns)
            df1[cols] = np.where(x[cols] > 0, c2, c1)
            return df1

        # change the function being used if wanting to do specific thing to whole row
        with pd.option_context('display.precision',2):
            final_html = df_to_styled_html(self.df,color_negative_red)

        return final_html
    