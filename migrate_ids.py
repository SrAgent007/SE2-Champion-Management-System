from database import get_connection

def run_migration():
    conn = get_connection()
    if not conn:
        print("Database connection failed.")
        return
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 1. Fetch all existing users, ordered by oldest first
        cursor.execute("SELECT user_id, employee_id, role FROM user ORDER BY user_id ASC")
        users = cursor.fetchall()
        
        counters = {"Admin": 1, "Staff": 1, "Worker": 1}
        prefix_map = {"Admin": "ADM", "Staff": "STF", "Worker": "WKR"}
        id_mapping = {} # To remember Old ID -> New ID
        
        print("--- UPDATING USERS ---")
        for u in users:
            role = u['role']
            # Fallback for unexpected roles
            if role not in counters: role = "Worker" 
            
            # Format: ROLE-2026-XXX
            new_id = f"{prefix_map[role]}-2026-{counters[role]:03d}"
            id_mapping[u['employee_id']] = new_id
            
            cursor.execute("UPDATE user SET employee_id = %s WHERE user_id = %s", (new_id, u['user_id']))
            counters[role] += 1
            print(f"Updated User: {u['employee_id']}  ➔  {new_id}")
            
        # 2. Update the Projects table (Because 'workers_assigned' uses employee_ids)
        print("\n--- UPDATING PROJECT ASSIGNMENTS ---")
        cursor.execute("SELECT project_id, workers_assigned FROM projects WHERE workers_assigned IS NOT NULL AND workers_assigned != ''")
        projects = cursor.fetchall()
        
        for p in projects:
            old_workers = p['workers_assigned'].split(',')
            new_workers = []
            for w in old_workers:
                w_strip = w.strip()
                # Replace the old ID with the new one
                new_workers.append(id_mapping.get(w_strip, w_strip))
                
            new_workers_str = ", ".join(new_workers)
            cursor.execute("UPDATE projects SET workers_assigned = %s WHERE project_id = %s", (new_workers_str, p['project_id']))
            print(f"Updated Project {p['project_id']} workers list.")
            
        conn.commit()
        print("\n✅ Migration Complete! All IDs are now formatted.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    run_migration()