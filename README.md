# ทีม: Gobblet XO
# สมาชิก:
- ยศวีร์ ศุภโชคธนาทรัพย์ 68114540474

## GOBBLET XO (Tactical Tic-Tac-Toe)
โครงงานกลุ่มรายวิชาการเขียนโปรแกรมเชิงวัตถุ (Final Team Project) พัฒนาโดยใช้ภาษา Python และ Pygame Framework

### วิธีการติดตั้ง (Installation)
1. ตรวจสอบว่ามี Python 3.13 ขึ้นไปในเครื่อง
2. ติดตั้ง Library ที่จำเป็น:
   ```bash
   pip install -r requirements.txt
   ```
   หรือใช้ `uv` (แนะนำ):
   ```bash
   uv sync
   ```

### วิธีการใช้งาน (Usage)
1. รันโปรแกรมหลัก:
   ```bash
   python src/main.py
   ```
2. เลือกโหมดการเล่นจากหน้าเมนู:
   - **Play vs AI**: เล่นกับบอท
   - **Host Game**: สร้างห้องเพื่อเล่นออนไลน์ในวง Network เดียวกัน
   - **Join Game**: เข้าร่วมห้องที่เพื่อนสร้างขึ้น

### การประยุกต์ใช้หลักการ OOP และ SOLID
- **Encapsulation**: มีการแยกตรรกะของ Board, Piece, และ Inventory ไว้ในคลาสที่ชัดเจน
- **Inheritance**: `GameController` สืบทอดมาจาก `Pygame` base class ใน `src/core/` เพื่อใช้โครงสร้างมาตรฐานของเกม
- **Polymorphism**: ใช้ `Player` เป็น abstract base class และมี `HumanPlayer`, `AIPlayer` เป็น subclasses ที่มีพฤติกรรมการเล่นที่ต่างกัน (Polymorphic `get_move`)
- **Composition**: `GameController` ประกอบด้วยวัตถุจากคลาส `UIManager`, `Board`, `NetworkManager` และ `Player`
- **SOLID (Liskov Substitution)**: สามารถสลับเปลี่ยนประเภทของ Player (Human/AI) ได้โดยไม่กระทบโครงสร้างหลักของเกม
