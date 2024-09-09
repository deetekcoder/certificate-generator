from flask import Flask, render_template, request, redirect, url_for, send_file
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import os
from flask_mail import Mail, Message

app = Flask(__name__)

# Ensure 'certificates' directory exists
if not os.path.exists('certificates'):
    os.makedirs('certificates')

# Configure email settings
app.config['MAIL_SERVER'] = 'md-in-74.webhostbox.net'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'info@prayogbharti.org'
app.config['MAIL_PASSWORD'] = 'Santa@123!'
app.config['MAIL_DEFAULT_SENDER'] = ('Certificate Sender', 'info@prayogbharti.org')

mail = Mail(app)

"""def cm_to_px(cm, dpi=300):
    return int(cm * dpi / 2.54)"""

def generate_certificate(data):
    template_path = 'templates/certificate_template.jpg'
    font_path = 'templates/arial.ttf'
    font_size = 35

    certificates = []

    for index, row in data.iterrows():
        img = Image.open(template_path)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(font_path, font_size)

        draw.text((1627, 180), str(row['Serial No']), font=font, fill='black')
        draw.text((793, 588), row['Name'], font=font, fill='black')
        draw.text((884, 655), row['Parents Name'], font=font, fill='black')
        draw.text((919, 730), row['Course'], font=font, fill='black')
        draw.text((526, 800), row['From'], font=font, fill='black')
        draw.text((888, 800), row['To'], font=font, fill='black')


        # Save the certificate as a PDF
        cert_filename = f"cert_{row['Serial No']}.pdf"
        img_path = os.path.join('certificates', cert_filename)
        img.save(img_path, "PDF")

        row['image_path'] = img_path  # Store image path for sending via email
        certificates.append(row)

    return certificates

def send_certificate_email(cert_holder):
    try:
        print(f"Preparing to send email to {cert_holder['email']}")
        msg = Message(f"Your Certificate - {cert_holder['Name']}",
                      recipients=[cert_holder['email']])
        
        msg.body = f"Dear {cert_holder['Name']},\n\nPlease find attached your certificate.\n\nBest regards,\nCertificate Team"
        
        with app.open_resource(cert_holder['image_path']) as fp:
            msg.attach(f"Certificate_{cert_holder['Serial No']}.pdf", "application/pdf", fp.read())
        
        mail.send(msg)
        print(f"Email sent to {cert_holder['email']} successfully!")
    except Exception as e:
        print(f"Failed to send email to {cert_holder['email']}. Error: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        try:
            data = pd.read_csv(file)
            print("CSV Data Loaded:", data)
            certificates = generate_certificate(data)
            print("Generated Certificates:", certificates)
            
            for cert_holder in certificates:
                if 'email' in cert_holder and cert_holder['email']:
                    send_certificate_email(cert_holder)

            return render_template('upload.html', certificates=certificates)
        except Exception as e:
            print(f"Error in processing: {e}")
            return redirect(url_for('index'))
    
    return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join('certificates', filename), as_attachment=True)

@app.route('/preview/<filename>')
def preview_file(filename):
    return send_file(os.path.join('certificates', filename), as_attachment=False)

if __name__ == '__main__':
    app.run(debug=True)
