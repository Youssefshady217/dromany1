import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="📄 قراءة أسماء الأدوية", layout="centered")
st.title("📄 استخراج بيانات الأدوية من ملف PDF")

uploaded_file = st.file_uploader("📤 ارفع ملف PDF", type=["pdf"])

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

    # 🟩 استخراج الأدوية مع منع التكرار بناءً على رقم الدواء
    lines = full_text.split("\n")
    med_list = []
    seen_numbers = set()

    for i in range(len(lines) - 1):
        combined_line = lines[i].strip() + " " + lines[i + 1].strip()

        # استخراج رقم الدواء (1-, 2-, ...)
        match_number = re.search(r"(\d+)-\s", combined_line)
        if not match_number:
            continue

        num = match_number.group(1)
        if num in seen_numbers:
            continue
        seen_numbers.add(num)

        # استخراج اسم الدواء
        match = re.search(r"\d-\s(.*?)(/|\s/\s|\s/\S)", combined_line)
        if match:
            med_name = match.group(1).strip()
        else:
            match_alt = re.search(r"\d-\s(.*?)(\d+\s|EGP|Box|time|ml|MG)", combined_line)
            if match_alt:
                med_name = match_alt.group(1).strip()
            else:
                match_basic = re.search(r"\d-\s(.*)", combined_line)
                if match_basic:
                    med_name = match_basic.group(1).strip()
                else:
                    continue

        # استخراج الكمية والسعر
        qty_match = re.search(r"EGP\s+\d+\.\d+\s+(\d+)", combined_line)
        price_match = re.search(r"(\d+\.\d+)\s+Box", combined_line)

        qty = float(qty_match.group(1)) if qty_match else 1.0
        unit_price = float(price_match.group(1)) if price_match else 0.0
        total_price = round(qty * unit_price, 2)

        med_list.append({
            "اسم الدواء": med_name,
            "الكمية": qty,
            "سعر الوحدة": unit_price,
            "سعر الكمية": total_price
        })

    # 🟩 عرض النتائج
    if med_list:
        df = pd.DataFrame(med_list)
        st.subheader("📋 جدول الأدوية المستخرجة:")
        st.dataframe(df)

        # زر تحميل Excel
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        st.download_button(
            label="⬇️ تحميل Excel",
            data=output,
            file_name="approved_meds.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("❌ لم يتم العثور على أسماء أدوية.")


