from flask import Flask, request, redirect, url_for, send_from_directory, render_template
import pandas as pd
import os
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def expand_post_code_range(post_code_range):
    if '-' in post_code_range:
        start, end = post_code_range.split('-')
        start_prefix = start[:2]
        start_suffix = start[2]
        end_prefix = end[:2]
        end_suffix = end[2]
        expanded = []

        if start_prefix[1] == end_prefix[1]:
            for c in range(ord(start_suffix), ord(end_suffix) + 1):
                expanded.append(f"{start_prefix[0]}{start_prefix[1]}{chr(c)}")
        else:
            for i in range(int(start_prefix[1]), int(end_prefix[1]) + 1):
                if i == int(start_prefix[1]):
                    for c in range(ord(start_suffix), ord('Z') + 1):
                        expanded.append(f"{start_prefix[0]}{i}{chr(c)}")
                elif i == int(end_prefix[1]):
                    for c in range(ord('A'), ord(end_suffix) + 1):
                        expanded.append(f"{end_prefix[0]}{i}{chr(c)}")
                else:
                    for c in range(ord('A'), ord('Z') + 1):
                        expanded.append(f"{start_prefix[0]}{i}{chr(c)}")
        return expanded
    else:
        return [post_code_range]


def get_area(postal_code, postal_code_to_area):
    if pd.isna(postal_code):
        return None
    postal_code = str(postal_code)
    prefix = postal_code[:3]
    return postal_code_to_area.get(prefix, None)


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], 'PostList.csv')
            file.save(filename)

            post_area_df = pd.read_csv('PostArea.csv')  # Hardcoded local file
            post_list_df = pd.read_csv(filename)

            postal_code_to_area = {}
            for _, row in post_area_df.iterrows():
                area = row['Area']
                post_code_ranges = re.split(r',\s*', row['PostCode'])
                for post_code_range in post_code_ranges:
                    expanded_post_codes = expand_post_code_range(post_code_range)
                    for post_code in expanded_post_codes:
                        postal_code_to_area[post_code] = area

            post_list_df['area'] = post_list_df['postal-code'].apply(get_area, postal_code_to_area=postal_code_to_area)
            output_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'UpdatedPostList.csv')
            post_list_df.to_csv(output_filename, index=False)
            return redirect(url_for('download_file', filename='UpdatedPostList.csv'))
    return render_template('index.html')


@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
