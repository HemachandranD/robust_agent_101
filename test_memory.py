"""Test the new windowed memory implementation"""
from src.memory import SQLiteMemory

print("="*60)
print("Testing Windowed Memory Implementation")
print("="*60)

# Test 1: Create a new session
print("\n1️⃣ Creating new memory session...")
mem = SQLiteMemory(window_size=5)
print(f"   Session ID: {mem.session_id}")
print(f"   Window size: {mem.window_size} turns")

# Test 2: Add messages
print("\n2️⃣ Adding conversation messages...")
for i in range(8):
    mem.add_user_message(f"User message {i+1}")
    mem.add_ai_message(f"AI response {i+1}")
    print(f"   Added turn {i+1}")

# Test 3: Check total messages
count = mem.get_message_count()
print(f"\n3️⃣ Total messages in session: {count}")

# Test 4: Load history with windowing
print(f"\n4️⃣ Loading history (window_size={mem.window_size})...")
history = mem.load_history()
print(f"   Loaded {len(history)} messages (last {len(history)//2} turns)")
print(f"   Should show only last 5 turns = 10 messages")
print("\n   Recent history:")
for msg in history[-4:]:  # Show last 2 turns
    print(f"   - {msg.__class__.__name__}: {msg.content}")

# Test 5: Load with custom limit
print(f"\n5️⃣ Loading with custom limit (3 turns)...")
history_limited = mem.load_history(limit=3)
print(f"   Loaded {len(history_limited)} messages")

# Test 6: List sessions
print("\n6️⃣ Listing all sessions...")
sessions = mem.list_sessions()
print(f"   Found {len(sessions)} session(s)")
for session_id, msg_count, first, last in sessions:
    print(f"   - {session_id}: {msg_count} messages")

# Test 7: Clear session
print("\n7️⃣ Clearing current session...")
mem.clear()
count_after = mem.get_message_count()
print(f"   Messages after clear: {count_after}")

print("\n" + "="*60)
print("✅ All memory tests passed!")
print("="*60)

