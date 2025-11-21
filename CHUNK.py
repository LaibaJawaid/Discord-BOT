import json
import re

# --- File Paths and Parameters ---
INPUT_CHAPTER_WISE_FILE = "chpWise.json"
OUTPUT_FINAL_CHUNKS_FILE = "final_Chunks.json"
MAX_CHUNK_SIZE = 1500  # Characters (approx 200-300 words)
CHUNK_OVERLAP = 150    # Characters

# --- Splitter Delimiters (Order matters) ---
split_delimiters = ["\n\n", "\n", ". ", " ", ""]

def get_chapter_name(text):
    """
    Chapter ke shuru se wife ka naam nikalta hai, 'Umm' jaise prefixes aur 
    Zaynab jaisi duplicate entries ko theek karta hai.
    Yeh function ab specific keywords (unique identifiers) search karta hai.
    """
    text_lower = text.lower()
    # Sirf shuruaati 200 characters ko check karein jahan title hota hai
    start_of_chapter = text_lower[:200] 

    # 1. Zaynab Disambiguation (Highest Priority)
    if 'zaynab bint khuzaymah' in start_of_chapter:
        return "Zaynab Khuzaymah"
    if 'zaynab bint jahsh' in start_of_chapter:
        return "Zaynab Jahsh"
        
    # 2. Umm Habībah (Must be tagged correctly)
    if 'umm habibah ramlah bint' in start_of_chapter:
        return "Ummhabibah" 
    
    # 3. Fallback for all other names using the robust prefix extraction
    # Pattern: 'umm al-muminin' ke baad, koi bhi name/word/char, uske baad 'bint'
    match = re.search(r'umm\s+al-muminin\s+([\w\s\*\’\'-]+)\s*bint', start_of_chapter, re.IGNORECASE)
    
    if match:
        name_part = match.group(1).strip()
        # Clean special characters and multiple spaces
        cleaned_name = re.sub(r'[\*,\.\'\"\(\)\-\’]', '', name_part).strip()
        words = cleaned_name.split()

        if not words:
            return "General Conclusion"

        primary_name = words[0].capitalize()
        
        # 'Umm' or 'Bint' prefix handling (e.g., Umm Salamah, only gets 'Salamah')
        if primary_name.lower() in ('umm', 'bint') and len(words) > 1:
            primary_name = words[1].capitalize()
        
        return primary_name

    # Final fallback
    return "General Conclusion"

def recursive_text_splitter(text, chapter_name, chunk_size, overlap):
    """
    Text ko recursively chote chunks mein todta hai, jahan sentence aur
    paragraph boundaries ko maintain kiya jaata hai.
    """
    
    # 1. Text ko sentences/paragraphs mein todna
    texts = [text]
    for delimiter in split_delimiters:
        new_texts = []
        for t in texts:
            if len(t) > chunk_size:
                new_texts.extend([item.strip() for item in t.split(delimiter) if item.strip()])
            else:
                new_texts.append(t)
        
        texts = new_texts
        texts = [t.strip() for t in texts if t.strip()]
        
        if all(len(t) <= chunk_size for t in texts):
            break

    final_chunks = []
    current_chunk = ""
    
    # 2. Tukdo ko jodkar final chunks banana (Overlap ke saath)
    for segment in texts:
        
        if len(current_chunk) + len(segment) + 1 > chunk_size:
            
            if current_chunk:
                final_chunks.append({
                    "wife_name": chapter_name,
                    "content": current_chunk.strip()
                })
            
            overlap_text = current_chunk[-overlap:].strip() if len(current_chunk) > overlap else ""
            current_chunk = overlap_text + " " + segment
            
        else:
            current_chunk += (" " if current_chunk else "") + segment
            
    # Last chunk ko save karo
    if current_chunk.strip():
        final_chunks.append({
            "wife_name": chapter_name,
            "content": current_chunk.strip()
        })
        
    return final_chunks

def process_and_chunk_chapters():
    """
    Chapter-wise file ko load karta hai, chunks mein todta hai, aur phir
    unko sirf JSON file mein save karta hai.
    """
    print(f"🔄 Loading data from: {INPUT_CHAPTER_WISE_FILE}...")
    try:
        with open(INPUT_CHAPTER_WISE_FILE, 'r', encoding='utf-8') as f:
            chapter_list = json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: {INPUT_CHAPTER_WISE_FILE} file nahin mili.")
        return
    except json.JSONDecodeError:
        print("❌ ERROR: JSON file format theek nahi hai.")
        return

    all_final_chunks = []
    
    for i, chapter_text in enumerate(chapter_list):
        if not chapter_text:
            continue
            
        chapter_name = get_chapter_name(chapter_text)
        
        # Chapter ko chote chunks mein todein
        chunks = recursive_text_splitter(chapter_text, chapter_name, MAX_CHUNK_SIZE, CHUNK_OVERLAP)
        all_final_chunks.extend(chunks)

    # --- Step 1: JSON File Output ---
    output_filename = "final_Chunks.json" # Use user's observed output filename for consistency
    
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(all_final_chunks, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ JSON file save karne mein galti: {e}")

    
    # --- Final Summary ---
    print("\n--- Final Chunking and Serialization Summary ---")
    print(f"✅ Total Chapters Processed: {len(chapter_list)}")
    print(f"✅ Total Final Embeddable Chunks Created: {len(all_final_chunks)}")
    print(f"💾 Output file saved to: {output_filename}")
    print("\n--- Validation Check ---")
    
    # Validation checks for the requested changes
    umm_habibah_chunk = next((chunk for chunk in all_final_chunks if chunk['wife_name'] == 'Ummhabibah'), None)
    zaynab_khuzaymah_chunk = next((chunk for chunk in all_final_chunks if chunk['wife_name'] == 'Zaynab Khuzaymah'), None)
    zaynab_jahsh_chunk = next((chunk for chunk in all_final_chunks if chunk['wife_name'] == 'Zaynab Jahsh'), None)


    if umm_habibah_chunk:
        print(f"✅ Umm Habībah chunk found. Tag used: {umm_habibah_chunk['wife_name']}")
    else:
        print("❌ Umm Habībah chunk not found or incorrectly tagged.")
        
    if zaynab_khuzaymah_chunk:
        print(f"✅ Zaynab Khuzaymah chunk found. Tag used: {zaynab_khuzaymah_chunk['wife_name']}")
    else:
        print("❌ Zaynab Khuzaymah chunk not found or incorrectly tagged.")
    
    if zaynab_jahsh_chunk:
        print(f"✅ Zaynab Jahsh chunk found. Tag used: {zaynab_jahsh_chunk['wife_name']}")
    else:
        print("❌ Zaynab Jahsh chunk not found or incorrectly tagged.")


# --- Execution ---
process_and_chunk_chapters()