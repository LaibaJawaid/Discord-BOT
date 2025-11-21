import json
import re

# --- File Paths ---
# Aapki pichli Super Cleaned file:
INPUT_CLEANED_FILE = "Newcleaned_data.json" 
OUTPUT_CHAPTER_WISE_FILE = "chpWise.json"

def normalize_and_clean_text_final(text):
    """
    Final aggressive cleaning function (Pichla code jismein citations aur junk hataya tha)
    """
    # 1. Lowercasing and Name Normalization (A'ishah -> aishah fix)
    text = text.lower()
    text = re.sub(r'[“\'~‘`’"]', '', text) 
    text = re.sub(r'[^\x00-\x7F]+', ' ', text) 
    
    # 2. Removal of OCR/Structural Garbage
    ocr_patterns = [
        r'pappve ptt: usliuls vou yell\)\s?mibaiall/clian y a piled\) billy delabsl jlo qylae',
        r'islamic inc\. oe neos ye pg eujpgiull slo', r'att\) bed! glee a', r'yavn evo: wsu fans 51475 favvan i-14 ov ce tel\. 3911961-3900572',
        r'wwayv/¥\. v6 lay\) aay', r'eh the wives ofthe prope muhammad 22 hie',
        r'isbn:\s?[\d-]+', r'all rights reserved\. no part of this publication.*'
    ]
    for pattern in ocr_patterns:
        text = re.sub(pattern, ' ', text)
    
    # 3. CRITICAL: Removal of ALL Citation/Reference/Stray Numbers and the user-noticed remaining noise
    text = re.sub(r'\[page_index\s*\d+\]', ' ', text) 
    text = re.sub(r'\s?\d+\.\s+[a-z\s,;-]+\s?(?:vol\. \d+|\d+ ah|al-quran|hadith|p\. \d+|al-masad|al-alac|an-nur)\s?\.', ' ', text)
    text = re.sub(r'(?:vol|p|pp)\.?\s?\d+(?:-\d+)?', ' ', text)
    citation_names = r'ibn hisham|an-nasharti|adh-dhahabi|ibn hajar|al-muttaqi al-hindi|ibn kathir|ibn sad|al-bukhari|muslim|as-suyuti|kanz al-ummal|fath al-bari|tabagat|siyar alam an-nubala|tafsir al-quran al-azhim|sirat ala-bayt an-nabi|al-isabah|al-jsabah|al-bidayah wa an-nihayah|al-itqan fi ulum al-quran|sirah an-nabawivyah|an-nikah|as-sayd wa az-zaba ih|at-tafsir'
    text = re.sub(citation_names, ' ', text)

    # 4. Removal of Common Islamic Honorifics and Structural Noise
    text = re.sub(r'\s?\(peace be upon him\)\s?', ' ', text)
    text = re.sub(r'\s?\(pbuh\)\s?', ' ', text)
    text = re.sub(r'\s?\(may allah be pleased with her/him\)\s?', ' ', text)
    
    # 5. Remove Surah and Ayah References
    text = re.sub(r'&.+?(?:al-alac|an-nur|al-masad|al-fath|al-ahzab):\s?\d+-\d+?\s?\)', ' ', text)
    text = re.sub(r'\s?\([\d\s\.,-]+\)\s?', ' ', text) 
    text = re.sub(r'\s?\([a-z\s]+:[\s\d-]+?\)\s?', ' ', text) 

    # 6. Clean up extra whitespace and newlines
    text = re.sub(r'[\n\r]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 7. CRITICAL FINAL PUNCTUATION CLEANUP
    text = re.sub(r'[\.]{2,}', '. ', text)
    text = re.sub(r'\s?,\s?\.', '. ', text)
    text = re.sub(r'\s?:\s*\.', '. ', text) 
    text = re.sub(r'^\s*[.,]\s*|\s*[.,]\s*$', ' ', text).strip()
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def create_chapter_wise_data_fixed():
    """
    Chapter title pattern ko zyada flexible banata hai aur chapters ko extract karta hai.
    """
    try:
        with open(INPUT_CLEANED_FILE, 'r', encoding='utf-8') as f:
            indexed_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: {INPUT_CLEANED_FILE} file nahin mila. Please check the file name.")
        return

    chapter_breaks = []
    # --- FLEXIBLE REGEX: Thode bahut extra characters ko ignore karega ---
    # Pattern: 'umm al-muminin' ke baad, koi bhi name/word ho sakta hai, uske baad 'bint' aaye.
    chapter_title_pattern = re.compile(r'^umm\s+al-muminin\s+([\w\s\*]+)\s*bint', re.IGNORECASE)
    
    for i, item in enumerate(indexed_data):
        # Cleaning function ko dobara chalao taaki title mein chupa hua junk nikal jaaye.
        temp_cleaned_text = normalize_and_clean_text_final(item['cleaned_text'].strip())
        
        match = chapter_title_pattern.match(temp_cleaned_text)
        if match:
            wife_name = match.group(1).replace(' ','').strip() # Name ko thoda aur clean karo
            # Agar 'khadijah' ya 'sawdah' ke baad 'aishah' aa raha hai, to iska matlab chapter break mil gaya.
            chapter_breaks.append({'start_index': i, 'wife_name': wife_name})
    
    # 2. Extract and Combine Chapter Text (Logic remains the same)
    final_chapter_list = []
    
    for i in range(len(chapter_breaks)):
        start_index = chapter_breaks[i]['start_index']
        end_index = chapter_breaks[i+1]['start_index'] if i + 1 < len(chapter_breaks) else len(indexed_data)
        wife_name = chapter_breaks[i]['wife_name']
        
        raw_chapter_text = " ".join([indexed_data[j]['cleaned_text'] for j in range(start_index, end_index)])
        
        # Super-aggressive cleaning (citation junk etc. hatao)
        cleaned_chapter_text = normalize_and_clean_text_final(raw_chapter_text)
        
        # Chapter ko uske name se shuru karo
        if cleaned_chapter_text:
            final_chapter_list.append(cleaned_chapter_text.strip())

    # 3. Save the Final Chapter List
    try:
        with open(OUTPUT_CHAPTER_WISE_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_chapter_list, f, indent=2, ensure_ascii=False)
        
        print("\n--- Process Summary (Chapter-Wise) ---")
        print(f"✅ Total Chapters Found and Cleaned (Final Attempt): {len(final_chapter_list)}")
        print(f"💾 File saved successfully to: {OUTPUT_CHAPTER_WISE_FILE}")
        
        # Chapter Names Verify karein
        found_names = [cb['wife_name'] for cb in chapter_breaks]
        print(f"Found Chapter Names: {found_names}")
        
        if 'aishah' in [name.lower() for name in found_names]:
            print("🎉 Confirmation: Aishah A.S. ka chapter ab mil gaya hai!")
        else:
            print("⚠️ Warning: Abhi bhi Aishah A.S. ka chapter title pattern se detect nahi ho paya. Manual check ki zaroorat pad sakti hai.")
            
        print("\n**NEXT STEP: Ab is 'final_chapter_wise_corpus_v2_fixed.json' file se embeddings generate karein.**")
    
    except Exception as e:
        print(f"❌ An error occurred while saving the chapters: {e}")

# --- Execution ---
create_chapter_wise_data_fixed()