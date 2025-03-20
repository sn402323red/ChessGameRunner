import chess
import chess.engine
import chess.pgn
import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk

def stockfish_move(board, engine):
    result = engine.play(board, chess.engine.Limit(time=2.0))
    return result.move

def board_to_canvas(board):
    canvas_board = [[None for _ in range(8)] for _ in range(8)]
    for row in range(8):
        for col in range(8):
            piece = board.piece_at(row * 8 + col)
            if piece:
                canvas_board[row][col] = piece
    return canvas_board

def draw_board(canvas, board, piece_images):
    canvas.delete("all")
    colors = ["white", "gray"]
    canvas_board = board_to_canvas(board)

    for row in range(8):
        for col in range(8):
            color = colors[(row + col) % 2]
            x1, y1 = col * 60, row * 60
            x2, y2 = x1 + 60, y1 + 60
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")
            piece = canvas_board[7-row][col]
            if piece:
                piece_image = piece_images[str(piece)]
                canvas.create_image(x1 + 30, y1 + 30, image=piece_image)

    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    for i in range(8):
        canvas.create_text(i * 60 + 30, 480, text=files[i], font=('Arial', 14, 'bold'))
        canvas.create_text(480, i * 60 + 30, text=str(8 - i), font=('Arial', 14, 'bold'))

def on_move_enter(board, entry, canvas, engine, root, piece_images, game_status, moves_textbox):
    move_str = entry.get()
    entry.delete(0, tk.END)

    if game_status['is_bot_turn']:
        messagebox.showinfo("Wait", "It's the bot's turn!")
        return

    try:
        move = chess.Move.from_uci(move_str)
        if move in board.legal_moves:
            # Clear the hint from the moves_textbox
            moves_textbox.tag_remove("hint", "1.0", "end")
            board.push(move)
            moves_textbox.insert(tk.END, f"Player: {move_str}\n")
            moves_textbox.see(tk.END)
            game_status['is_bot_turn'] = True
            draw_board(canvas, board, piece_images)
            root.after(100, make_bot_move, board, canvas, engine, root, piece_images, game_status, moves_textbox)
        else:
            messagebox.showerror("Invalid Move", "The move is not valid.")
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid move in UCI format (e.g., e2e4).")

def undo_move(board, canvas, piece_images, moves_textbox):
    if len(board.move_stack) >= 2:
        board.pop()
        board.pop()
        moves_textbox.delete("end - 24 chars", tk.END)
        draw_board(canvas, board, piece_images)
    else:
        messagebox.showinfo("Undo", "No moves to undo!")

def make_bot_move(board, canvas, engine, root, piece_images, game_status, moves_textbox):
    if board.is_game_over():
        game_over_message(board.result())
        return

    move = stockfish_move(board, engine)
    board.push(move)
    moves_textbox.insert(tk.END, f"Bot: {move}\n")
    moves_textbox.see(tk.END)
    game_status['is_bot_turn'] = False
    draw_board(canvas, board, piece_images)
    
    if board.is_game_over():
        game_over_message(board.result())

def game_over_message(result):
    messagebox.showinfo("Game Over", f"Game over!\nResult: {result}")

def end_game(root):
    if messagebox.askyesno("End Game", "Are you sure you want to end the game?"):
        messagebox.showinfo("Game Over", "Game has been ended.")
        root.destroy()

def analyze_moves(board, engine, moves_textbox, canvas, frame, piece_images):
    moves = list(board.move_stack)
    board.clear_stack()
    board.reset()

    for move in moves:
        try:
            board.push(move)
            info = engine.analyse(board, chess.engine.Limit(time=0.1))
            score = info["score"].relative
            moves_textbox.insert(tk.END, f"Move: {move}, Score: {score}\n")
        except AssertionError:
            messagebox.showerror("Analysis Error", f"Invalid move {move} encountered during analysis.")
            break
    moves_textbox.see(tk.END)

    # Add buttons for replay controls
    prev_button = tk.Button(frame, text="Previous Move", command=lambda: replay_move(board, canvas, piece_images, moves, -1))
    prev_button.grid(row=5, column=0, pady=10)

    replay_button = tk.Button(frame, text="Start Replay", command=lambda: start_replay(board, canvas, piece_images, moves))
    replay_button.grid(row=5, column=1, pady=10)

    next_button = tk.Button(frame, text="Next Move", command=lambda: replay_move(board, canvas, piece_images, moves, 1))
    next_button.grid(row=5, column=2, pady=10)

def display_pgn(board, moves_textbox):
    pgn = chess.pgn.Game.from_board(board)
    moves_textbox.insert(tk.END, f"\nPGN:\n{pgn}\n")
    moves_textbox.see(tk.END)

def get_hint(board, engine, moves_textbox):
    info = engine.analyse(board, chess.engine.Limit(time=2.0))
    best_move = info["pv"][0]
    moves_textbox.insert(tk.END, f"Hint: {best_move}\n", "hint")
    moves_textbox.tag_add("hint", "end-2l", "end-1l")
    moves_textbox.see(tk.END)

def replay_move(board, canvas, piece_images, moves, direction):
    if not hasattr(replay_move, "index"):
        replay_move.index = 0

    replay_move.index += direction
    replay_move.index = max(0, min(replay_move.index, len(moves)))

    board.reset()
    for move in moves[:replay_move.index]:
        board.push(move)
    draw_board(canvas, board, piece_images)

def start_replay(board, canvas, piece_images, moves):
    board.reset()
    replay_move.index = 0
    replay_move(board, canvas, piece_images, moves, 1)

def play_game_gui():
    board = chess.Board()
    engine = chess.engine.SimpleEngine.popen_uci("stockfishmain.exe")
    root = tk.Tk()
    root.title("Chess Game")
    root.resizable(False, False)
    root.focus_force()

    global frame
    frame = tk.Frame(root)
    frame.pack()

    canvas = tk.Canvas(frame, width=520, height=520)
    canvas.grid(row=0, column=0, columnspan=2)

    moves_textbox = scrolledtext.ScrolledText(frame, height=20, width=25, state="normal")
    moves_textbox.grid(row=0, column=2, padx=10, rowspan=4)
    moves_textbox.tag_configure("hint", foreground="blue")

    piece_images = {
        "P": ImageTk.PhotoImage(Image.open("images/wp.png").resize((60, 60))),
        "N": ImageTk.PhotoImage(Image.open("images/wn.png").resize((60, 60))),
        "B": ImageTk.PhotoImage(Image.open("images/wb.png").resize((60, 60))),
        "R": ImageTk.PhotoImage(Image.open("images/wr.png").resize((60, 60))),
        "Q": ImageTk.PhotoImage(Image.open("images/wq.png").resize((60, 60))),
        "K": ImageTk.PhotoImage(Image.open("images/wk.png").resize((60, 60))),
        "p": ImageTk.PhotoImage(Image.open("images/bp.png").resize((60, 60))),
        "n": ImageTk.PhotoImage(Image.open("images/bn.png").resize((60, 60))),
        "b": ImageTk.PhotoImage(Image.open("images/bb.png").resize((60, 60))),
        "r": ImageTk.PhotoImage(Image.open("images/br.png").resize((60, 60))),
        "q": ImageTk.PhotoImage(Image.open("images/bq.png").resize((60, 60))),
        "k": ImageTk.PhotoImage(Image.open("images/bk.png").resize((60, 60))),
    }

    move_entry = tk.Entry(frame, width=10)
    move_entry.grid(row=1, column=0, pady=10, padx=0)

    move_button = tk.Button(frame, text="Submit Move", command=lambda: on_move_enter(board, move_entry, canvas, engine, root, piece_images, game_status, moves_textbox))
    move_button.grid(row=1, column=1, pady=10, padx=0)

    undo_button = tk.Button(frame, text="Undo Move", command=lambda: undo_move(board, canvas, piece_images, moves_textbox))
    undo_button.grid(row=2, column=0, columnspan=2, pady=10)

    hint_button = tk.Button(frame, text="Hint", command=lambda: get_hint(board, engine, moves_textbox))
    hint_button.grid(row=3, column=0, columnspan=2, pady=10)

    analysis_button = tk.Button(frame, text="Analysis", command=lambda: analyze_moves(board, engine, moves_textbox, canvas, frame, piece_images))
    analysis_button.grid(row=4, column=2, pady=10)

    end_game_button = tk.Button(frame, text="End Game", command=lambda: end_game(root))
    end_game_button.grid(row=5, column=2, pady=10)

    game_status = {'is_bot_turn': False}
    draw_board(canvas, board, piece_images)
    root.mainloop()

if __name__ == "__main__":
    play_game_gui()