from re import match, findall, sub, search, MULTILINE
from json import loads

class Hl:
	class Database:
		with open("events/highlighter/database.json", "r", encoding="utf-8") as db:
			database_content = loads(db.read())
		color_codes = database_content["color_codes"]
		commands = database_content["commands"]
		color_classes = database_content["color_classes"]

	def lex(self, func):
		state = {
			"mode": "normal",
			"history": ["normal"],
			"string_type": "",
			"is_macro": "",
		}
		def reset_token(need_to_append_char=False):
			nonlocal tokens, curr_token
			tokens.append(curr_token) if curr_token != "" else None
			if need_to_append_char:
				tokens.append(char)
			curr_token = ""
		def switch_mode(mode):
			if mode == "back":
				state["history"].pop(-1)
				state["mode"] = state["history"][-1]
			else:
				state["mode"] = mode
				state["history"].append(mode)
		# Setting up vars
		closed_brackets = {"{":"}", "[":"]"}
		tokens = []
		curr_token = ""
		# Magic
		for idx, char in enumerate(func):
			next_char = func[idx+1:idx+2]
			# prev_char = func[idx-1]
			prev_tokens = tokens[::-1]
			next_chars = func[idx+1:]
			if state["mode"] == "normal":
				if char not in " \\\n\t#[]{}.\"'$":
					curr_token += char
				else:
					need_to_append_char = True
					need_to_reset = True
					if char == "[":
						if "@" in curr_token:
							switch_mode("filter")
						else:
							switch_mode("component")
					elif char == "{":
						switch_mode("nbt")
						opened_brackets = 1
						state["nbt_type"] = char
					elif char == "$":
						need_to_reset = False
						if next_char == "(":
							switch_mode("macro")
							reset_token()
						curr_token += char
					elif char in "\"'":
						switch_mode("string")
						state["string_type"] = char
						curr_token += char
						need_to_reset = False
					elif char == ".":
						if curr_token == char:
							curr_token += char
						else:
							if next_char == char:
								reset_token()
								curr_token = char
								need_to_reset = False
							else:
								curr_token += char
								need_to_reset = False
						need_to_append_char = False
					elif char == "#":
						is_comment = [True] if prev_tokens == [] or "\n" not in prev_tokens else [True if i == '\n' else False for i in prev_tokens if i not in " \t"]
						next_word = next_chars.split(" ")[0]
						if is_comment[0] and not any([True for command in ["define", "declare", "alias"] if command == next_word]):
							switch_mode("comment")
							reset_token()
							curr_token += "\u200b"
						curr_token += char
						need_to_reset = False
					if need_to_reset:
						reset_token(need_to_append_char)
			elif state["mode"] == "filter":
				if char not in " \t{}\"']$)\\\n=,.":
					curr_token += char
				else:
					need_to_append_char = True
					need_to_reset = True
					if char == "]":
						switch_mode("back")
					elif char == "{":
						if tokens[-2] == "nbt":
							opened_brackets = 1
							switch_mode("nbt")
					elif char in "\"'":
						switch_mode("string")
						state["string_type"] = char
						curr_token += char
						need_to_reset = False
					elif char == ".":
						if curr_token == char:
							curr_token += char
						else:
							if next_char == char:
								reset_token()
								curr_token = char
								need_to_reset = False
							else:
								curr_token += char
								need_to_reset = False
						need_to_append_char = False
					elif char == "$":
						need_to_reset = False
						if next_char == "(":
							switch_mode("macro")
							reset_token()
						curr_token += char
					if need_to_reset:
						reset_token(need_to_append_char)
			elif state["mode"] == "macro":
				curr_token += char
				if char == ")":
					switch_mode("back")
					reset_token()
			elif state["mode"] == "component":
				if char not in " \\\n\t[]{}\"'$;,=":
					curr_token += char
				else:
					need_to_append_char = True
					need_to_reset = True
					if char in "{[":
						switch_mode("nbt")
						opened_brackets = 1
						state["nbt_type"] = char
					elif char in "\"'":
						switch_mode("string")
						state["string_type"] = char
						curr_token += char
						need_to_reset = False
					elif char == "$":
						need_to_reset = False
						if next_char == "(":
							switch_mode("macro")
							reset_token()
						curr_token += char
					if need_to_reset:
						reset_token(need_to_append_char)
				# Exiting component state if it closed
				if char == "]":
					switch_mode("back")
			elif state["mode"] == "nbt":
				if char not in " \t[]{}\"'$)\\\n;:,":
					curr_token += char
				else:
					need_to_append_char = True
					need_to_reset = True
					if char in "\"'":
						switch_mode("string")
						state["string_type"] = char
						curr_token += char
						need_to_reset = False
					elif char == "$":
						need_to_reset = False
						if next_char == "(":
							switch_mode("macro")
							reset_token()
						curr_token += char
					if need_to_reset:
						reset_token(need_to_append_char)
				# Exiting nbt state if it closed
				if char == state["nbt_type"]:
					opened_brackets += 1
				elif char == closed_brackets[state["nbt_type"]]:
					opened_brackets -= 1
					if opened_brackets == 0:
						switch_mode("back")
			elif state["mode"] == "string":
				curr_token += char
				if char == state["string_type"] and curr_token[-2] != "\\":
					switch_mode("back")
					reset_token()
			elif state["mode"] == "comment":
				if char != "\n":
					curr_token += char
				else:
					switch_mode("back")
					reset_token(True)
			if idx+1 == len(func) and curr_token != "":
				tokens.append(curr_token)
				break
		return tokens

	def highlight(self, func, theme="default"):
		# Shortcuts
  
		# the "shut up" type
		colours: dict[str, str] = Hl.Database.color_codes # if theme == "default" else theme
		commands = Hl.Database.commands
		# Setting up vars
		# commands_count = 0
		possible_subcommands = []
		bracket_index = 0
		highlighted = ""
		# Магія ✨
		tokens = Hl.lex(self, func)
		clear_tokens = tokens[:]
		# god sorry me for that
		for _ in range(clear_tokens.count(" ")):
			clear_tokens.remove(" ")
		for _ in range(clear_tokens.count("\\")):
			clear_tokens.remove("\\")
		for _ in range(clear_tokens.count("\n")):
			clear_tokens.remove("\n")
		for _ in range(clear_tokens.count("\t")):
			clear_tokens.remove("\t")
		clear_tokens.append('')
		clear_index = 0
  
		for index, token in enumerate(tokens):
			prev_tokens = tokens[index::-1]
			clear_index += 1 if token not in " \\\n\t" else 0
			next_clear_tokens = clear_tokens[clear_index:]
			prev_clear_tokens = clear_tokens[clear_index-2::-1]
			# fut_tokens = tokens[index+1:]
			if token[0] == "\u200b":
				token = token[1:]
				comment_content = sub(r"^\s*#(#|>)?", "", token, flags=MULTILINE)
				edited_content = comment_content[:]
				if token[1] in "#>":
					comment_type = "link-comment"
				else:
					comment_type = "comment"
				# path and @this stuff
				paths = findall(r"#[a-zA-z_\-]+:[a-zA-z_\-/]", comment_content)
				decorator_maybe_idk_honestly = findall(r"@\w+", comment_content)
				for path in paths:
					edited_content = comment_content.replace(path, colours["path"] + path + colours[comment_type])
				for i in decorator_maybe_idk_honestly:
					edited_content = edited_content.replace(i, colours["subcommand"] + i + colours[comment_type])
				#
				highlighted += colours["comment"] + token.replace(comment_content, "") + (colours[comment_type] if comment_type == "link-comment" else "") + edited_content
			elif token in possible_subcommands and bracket_index <= 0:
				highlighted += colours["subcommand"] + token
			elif (raw_command:=token.replace("$", "")) in commands and bracket_index <= 0:
				if raw_command != "execute":
					possible_subcommands = []
				highlighted += (colours["macro_bf_command"]+"$" if "$" in token else "") + colours["command"] + raw_command
				possible_subcommands += commands[raw_command]["subcommands"]
			elif token[0] in "\"'":
				# Highlighting macros
				macros = findall(r"\$\([0-9A-z-_\.]+\)", token)
				for macro in macros:
					token = token.replace(macro, macro.replace("$", colours["macro"]+"$")\
					.replace("(", colours[f"bracket{bracket_index}"]+"("+colours["text"])\
					.replace(")", colours[f"bracket{bracket_index}"]+")"+colours["string"]))
				#
				highlighted += colours["string"] + token
			elif token == "..":
				highlighted += colours["range"] + token
			elif ":" in token and token != ":" and next_clear_tokens[0] != "=":
				highlighted += colours["path"] + token
			elif token[0] in "@#$%." and len(token) > 1 and token[1] != "(" and prev_tokens[0] != "]":
				highlighted += colours["selector"] + token
			elif token in ":;=,":
				highlighted += colours["separator"] + token
			elif token in "[{(":
				highlighted += colours[f"bracket{bracket_index%3}"] + token
				bracket_index += 1
			elif token in ")}]":
				bracket_index -= 1
				highlighted += colours[f"bracket{bracket_index%3}"] + token
			elif match(r"^(~-?[0-9]*\.?[0-9]*|\^-?[0-9]*\.?[0-9]*|-?[0-9]+\.?[0-9]*[bsdf]?|-?\.?[0-9]+[bsdf]?)$", token):
				highlighted += colours["number"] + token
			elif match(r"\$\([0-9A-z-_\.]+\)", token):
				highlighted += f"{colours['macro']}${colours[f'bracket{bracket_index}']}({colours['text']}{token[2:-1]}{colours[f'bracket{bracket_index}']})"
			elif token == "\\":
				highlighted += colours["backslash"] + token
			elif token in " \t\n":
				highlighted += token
			else:
				text_type = "text"
				if bracket_index > 0:
					text_type = "key"
					if prev_clear_tokens[1] in ":=":
						text_type = "value"
				highlighted += colours[text_type] + token
		return highlighted

	def ansi2html(self, function):
		color_classes = Hl.Database.color_classes
		ansi_codes_re = r'(([30][0-7]?)(;(4[0-7]))?m)'
		converted = ""
		function_elements = function.replace("\n", "<br>").split("\u001b[")[1:]
		for element in function_elements:
			matches = search(ansi_codes_re, element)

			if matches is None:
				return # not sure what to do here
   
			converted += f'<span class="ansi_{color_classes[matches.group(2)]}{" "+color_classes[matches.group(4)] if matches.group(4) is not None else ""}">{element.replace(matches.group(1), "")}</span>'
		return f"<pre>{converted}</pre>"
