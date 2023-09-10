from tkinter import StringVar, TOP
from tkinterdnd2 import TkinterDnD, DND_ALL
import customtkinter as ctk
import sys,os,io
from PIL import Image
import signal
import time
import threading
from modules.rss import rssparser, opmlparser, opmladd, translate
from modules.research import research
import webbrowser
import json


class Tk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

class TextWidgetStream(io.TextIOBase):
    def __init__(self, widget):
        self.widget = widget

    def write(self, msg):
        self.widget.configure(state='normal')
        self.widget.insert('end', msg)
        self.widget.configure(state='disabled')
        self.widget.see('end')

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.opmlfile = self.opmlcheck()
        self.current_year = time.strftime("%Y")

        self.title("RSS Tool - hante")
        self.x = (self.winfo_screenwidth() - self.winfo_reqwidth()) / 2
        self.y = (self.winfo_screenheight() - self.winfo_reqheight()) / 2
                
        self.geometry("+%d+%d" % (self.x, self.y))
        self.language = "en"
        self.languagesearch = "All"
        self.languagetranslation = "None"
        self.dateoption = "All"
        self.number_outputs = 100
        self.toplevel_window = False
        
        signal.signal(signal.SIGINT, self.handle_interrupt)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.logo_image = ctk.CTkImage(Image.open("data/images/rsslogo.png"), size=(26, 26))
        self.rsssearcher_image = ctk.CTkImage(Image.open("data/images/rsssearcher.png"), size=(550, 150))
        self.rssparser_image = ctk.CTkImage(Image.open("data/images/rssparser.png"), size=(550, 150))
        self.opmlsettings_image = ctk.CTkImage(Image.open("data/images/opmlsettings.png"), size=(550, 150))
        self.image_icon_image = ctk.CTkImage(Image.open("data/images/image_icon_light.png"), size=(20, 20))
        self.home_image = ctk.CTkImage(light_image=Image.open("data/images/home_dark.png"), dark_image=Image.open("data/images/home_light.png"), size=(20, 20))
        self.chat_image = ctk.CTkImage(light_image=Image.open("data/images/chat_dark.png"), dark_image=Image.open("data/images/chat_light.png"), size=(20, 20))
        self.add_user_image = ctk.CTkImage(light_image=Image.open("data/images/add_user_dark.png"), dark_image=Image.open("data/images/add_user_light.png"), size=(20, 20))

        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(4, weight=1)

        self.navigation_frame_label = ctk.CTkLabel(self.navigation_frame, text="  RSS Tool", image=self.logo_image,
                                                             compound="left", font=ctk.CTkFont(size=15, weight="bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        self.home_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="RSS Searcher",
                                                   fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                   image=self.home_image, anchor="w", command=self.home_button_event)
        self.home_button.grid(row=1, column=0, sticky="ew")

        self.frame_2_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="RSS Parser",
                                                      fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                      image=self.chat_image, anchor="w", command=self.frame_2_button_event)
        self.frame_2_button.grid(row=2, column=0, sticky="ew")

        self.frame_3_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="OPML Settings",
                                                      fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                      image=self.add_user_image, anchor="w", command=self.frame_3_button_event)
        self.frame_3_button.grid(row=3, column=0, sticky="ew")

        self.appearance_mode_menu = ctk.CTkOptionMenu(self.navigation_frame, values=["Light", "Dark", "System"], command=self.change_appearance_mode_event, fg_color="#469d54", button_color="#3d8e47" ,button_hover_color="#2a5c33")
        self.appearance_mode_menu.grid(row=6, column=0, padx=20, pady=20, sticky="s")


# ---------------------- HOME FRAME ----------------------
        self.home_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_frame.grid_columnconfigure(0, weight=1)

        image_frame = ctk.CTkFrame(self.home_frame, fg_color="transparent")
        image_frame.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")

        self.home_frame_large_image_label = ctk.CTkLabel(image_frame, text="", image=self.rsssearcher_image)
        self.home_frame_large_image_label.pack()

        search_frame = ctk.CTkFrame(self.home_frame, fg_color="transparent")
        search_frame.grid(row=1, column=0, padx=(30,10), pady=10, sticky="nsew")

        self.entry = ctk.CTkEntry(search_frame, width=120)
        self.entry.pack(side="left", padx=(0, 5))
        
        self.entry.bind('<Return>', lambda event: self.searchgui())

        self.home_frame_button_2 = ctk.CTkButton(search_frame, text="Search", image=self.image_icon_image, compound="right", command=self.searchgui, fg_color="#469d54", hover_color="#2a5c33")
        self.home_frame_button_2.pack(side="left", padx=20)
        
        self.home_frame_button_3 = ctk.CTkButton(search_frame, text="Clear", image=self.image_icon_image, compound="right", command=self.clear, fg_color="#469d54", hover_color="#2a5c33")
        self.home_frame_button_3.pack(side="left", padx=(0,20))
        
        self.number_outputs_menu = ctk.CTkOptionMenu(self.home_frame, values=["100","200","300","400","500"], command=self.number_outputs_func, fg_color="#469d54", button_color="#3d8e47" ,button_hover_color="#2a5c33", width=10)
        self.number_outputs_menu.grid(row=1, column=0, padx=(500,10), sticky="w")
        
        self.language_option_menu_translation = ctk.CTkOptionMenu(self.home_frame, values=["None","English","French","Italian","Spanish","Russian"], command=self.languageoptiontranslation, fg_color="#469d54", button_color="#3d8e47" ,button_hover_color="#2a5c33")
        self.language_option_menu_translation.grid(row=1, column=0, padx=(0,420), sticky="e")
        
        self.language_option_menu_label = ctk.CTkLabel(self.home_frame, text="Sort by:")
        self.language_option_menu_label.grid(row=1, column=0, padx=(0,350), sticky="e")
        
        self.language_option_menu_search = ctk.CTkOptionMenu(self.home_frame, values=["All","English","French","Italian","Spanish","Russian"], command=self.languageoptionsearch, fg_color="#469d54", button_color="#3d8e47" ,button_hover_color="#2a5c33")
        self.language_option_menu_search.grid(row=1, column=0, padx=(0,35), sticky="e")
        
        self.language_option_menu_date = ctk.CTkOptionMenu(self.home_frame, values=["All","< "+self.current_year,"< "+str(int(self.current_year)-1),"< "+str(int(self.current_year)-2),"< "+str(int(self.current_year)-3),"< "+str(int(self.current_year)-4)], command=self.dateoptionfilter, fg_color="#469d54", button_color="#3d8e47" ,button_hover_color="#2a5c33")
        self.language_option_menu_date.grid(row=1, column=0, padx=(0,195), sticky="e")

        output_frame = ctk.CTkFrame(self.home_frame, fg_color="transparent")
        output_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        self.search_output_text = ctk.CTkTextbox(output_frame, width=self.x+290, height=self.y+80)
        self.search_output_text.pack(padx=10, pady=10, side="left", expand=True, fill="both")
        self.search_output_text.configure(state='disabled', font=('Calibri', 13))
        
        self.search_output_text2 = ctk.CTkTextbox(output_frame, width=self.x/2.5, height=self.y)


# ---------------------- FRAME 2 ----------------------
        self.second_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.second_frame.grid_columnconfigure(0, weight=1)

        image_frame = ctk.CTkFrame(self.second_frame, fg_color="transparent")
        image_frame.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")

        self.second_frame_large_image_label = ctk.CTkLabel(image_frame, text="", image=self.rssparser_image)
        self.second_frame_large_image_label.pack()

        rss_frame = ctk.CTkFrame(self.second_frame, fg_color="transparent")
        rss_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        self.rssbutton = ctk.CTkButton(rss_frame, text='Start', image=self.image_icon_image, compound="right", font=('Calibri', 12), command=self.rssparsergui, fg_color="#469d54", hover_color="#2a5c33")
        self.rssbutton.pack(side = "left", padx=25)
        
        self.language_option_menu = ctk.CTkOptionMenu(self.second_frame, values=["English","French","Italian","Spanish","Russian"], command=self.languageoption, fg_color="#469d54", button_color="#3d8e47" ,button_hover_color="#2a5c33")
        self.language_option_menu.grid(row=1, column=0, padx=220, pady=20, sticky="w")

        self.progressbar = ctk.CTkProgressBar(self.second_frame, width=(self.x/1.1)-10, height=17, progress_color="#469d54", mode="determinate")
        self.progressbar.set(0)
        self.progressbar.grid(row=1, column=0, padx=(400,35), pady=10, sticky="we")
        
        output_frame = ctk.CTkFrame(self.second_frame, fg_color="transparent")
        output_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        self.rss_output_text = ctk.CTkTextbox(output_frame, width=self.x+290, height=self.y+60)
        self.rss_output_text.pack(padx=10, pady=10, expand=True, fill="both")
        self.rss_output_text.configure(state='disabled', font=('Calibri', 13))
        self.rss_output_stream = TextWidgetStream(self.rss_output_text)
    
        

# ---------------------- FRAME 3 ----------------------
        self.third_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.third_frame.grid_columnconfigure(0, weight=1)
        
        image_frame = ctk.CTkFrame(self.third_frame, fg_color="transparent")
        image_frame.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")

        self.third_frame_large_image_label = ctk.CTkLabel(image_frame, text="", image=self.opmlsettings_image)
        self.third_frame_large_image_label.pack()
        
        search_frame_url = ctk.CTkFrame(self.third_frame, fg_color="transparent", width=self.x+290, height=self.y+60)
        search_frame_url.grid(row=1, column=0, padx=45, pady=10, sticky="nsew")

        titlelabel = ctk.CTkLabel(search_frame_url, text="Title :")
        titlelabel.pack(side="left", padx=(5,10))

        self.title_url = ctk.CTkEntry(search_frame_url, width=120)
        self.title_url.pack(side="left", padx=(0, 5))
        
        urllabel = ctk.CTkLabel(search_frame_url, text="RSS URL :")
        urllabel.pack(side="left", padx=10)
        
        self.entry_url = ctk.CTkEntry(search_frame_url, width=240)
        self.entry_url.pack(side="left", padx=(0, 5))
        
        self.title_url.bind('<Return>', lambda event: self.opmladdsource())
        self.entry_url.bind('<Return>', lambda event: self.opmladdsource())

        self.url_frame_button_2 = ctk.CTkButton(search_frame_url, text="Add feed", image=self.image_icon_image, compound="right", command=self.opmladdsource, fg_color="#469d54", hover_color="#2a5c33")
        self.url_frame_button_2.pack(side="left", padx=20)


        output_frame_url = ctk.CTkFrame(self.third_frame, fg_color="transparent", width=self.x+290, height=self.y+60)
        output_frame_url.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        self.search_output_text_url = ctk.CTkTextbox(output_frame_url)
        self.search_output_text_url.pack(padx=10, pady=10, expand=True, fill="both")
        self.search_output_text_url.configure(state='disabled', font=('Calibri', 13), width=self.x+290, height=self.y+80)
        
        self.opmlchoice_button = ctk.CTkButton(search_frame_url, text="OPML File", image=self.image_icon_image, compound="right", command=self.opmlchoice, fg_color="#469d54", hover_color="#2a5c33")
        self.opmlchoice_button.pack(side="right", padx=(25,0))

                

# ---------------------- FUNCTIONS ----------------------

        self.select_frame_by_name("home")

    def select_frame_by_name(self, name):
        self.home_button.configure(fg_color=("gray75", "gray25") if name == "home" else "transparent")
        self.frame_2_button.configure(fg_color=("gray75", "gray25") if name == "frame_2" else "transparent")
        self.frame_3_button.configure(fg_color=("gray75", "gray25") if name == "frame_3" else "transparent")


        if name == "home":
            self.home_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.home_frame.grid_forget()
        if name == "frame_2":
            self.second_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.second_frame.grid_forget()
        if name == "frame_3":
            self.third_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.third_frame.grid_forget()


    def handle_interrupt(self, signum, frame):
        try:
            self.root.destroy()
        except:
            pass
        self.destroy()
        
    def home_button_event(self):
        self.select_frame_by_name("home")

    def frame_2_button_event(self):
        self.select_frame_by_name("frame_2")

    def frame_3_button_event(self):
        self.select_frame_by_name("frame_3")

    def change_appearance_mode_event(self, new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode)
        
   
    def search_thread_func(self):
        i=0
        if os.path.isfile('data/rssdb.db'):
            self.res = research(self.entry.get(),self.languagesearch,self.dateoption)
            if self.res[0] != "No results found.":
                self.sourcecheck = [False] * len(self.res)
                self.frame_buttons = ctk.CTkScrollableFrame(self.search_output_text, fg_color="transparent", width=self.x-290)
                self.frame_buttons.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")
                for i in range(len(self.res)):
                    if i < self.number_outputs:
                        button = ctk.CTkButton(self.frame_buttons, 
                                            text=self.res[i][1]+" - "+self.res[i][0]+" : "+self.res[i][2]+'\t',
                                            command=lambda i=i: self.open_toplevel(self.res[i][0],self.res[i][2],self.res[i][3],self.res[i][1],self.res[i][4],self.res[i][5],i) if i < len(self.res) else None,
                                            fg_color="gray25",
                                            hover_color="gray75")
                        button.grid(row=i, column=1, padx = 10, pady = 5, sticky="nsew")
                    i+=1
                self.search_output_text.delete('1.0', 'end')
                self.search_output_text.configure(state='disabled')
                self.frame_buttons.grid_columnconfigure(1, weight=1)
                self.frame_buttons.grid_propagate()
            else:
                self.search_output_text.delete('1.0', 'end')
                self.search_output_text.insert('1.0', 'No results found.')
                self.search_output_text.configure(state='disabled')
                try:
                    self.frame_buttons.grid_remove()
                except:
                    pass
                self.deletepack()
                
        else:
            self.search_output_text.delete('1.0', 'end')
            self.search_output_text.insert('1.0', 'No database found. Please run the RSS Parser first.')
            self.search_output_text.configure(state='disabled')
            self.frame_buttons.grid_remove()
            self.deletepack()
            

    def open_toplevel(self,source,name,content,date,language,url,index):  
        self.urlcallback = url
        self.search_output_text2.pack(padx=10, pady=10, side="right", expand=True, fill="both")
        self.search_output_text2.configure(state='disabled', font=('Calibri', 13))
        
        savename = name
        savecontent = content
        
        frame = ctk.CTkFrame(self.search_output_text2, width=self.x/2, fg_color="transparent")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        if len(source) > 32:
            source = source[:32]+"..."
        var1 = ctk.StringVar(value=source)
        label = ctk.CTkLabel(frame, textvariable=var1, font=("Calibri", 13), fg_color="gray20", corner_radius=5)
        label.grid(row=2, column=0, padx=5, pady=10, sticky="nsew")

        if self.languagetranslation != "None" and "translated" in language and language != language.split(")")[-2].split("-")[-1][-2:]:
            try:
                languageoutput = language.split(")")[-2].split("-")[-1][-2:]
                translatedtext = translate([name,content],languageoutput,self.languagetranslation)
                name = translatedtext[0]
                content = translatedtext[1]
                print("✅ Translation from "+languageoutput+" to "+self.languagetranslation+" done.")
            except:
                print("❌ No model for this language")
                
        elif self.languagetranslation != "None" and "translated" not in language and language[:2] != self.languagetranslation:  
            try:
                translatedtext = translate([name,content],language[:2],self.languagetranslation)
                name = translatedtext[0]
                content = translatedtext[1]
                print("✅ Translation from "+language[:2]+" to "+self.languagetranslation+" done.") 
            except:
                print("❌ No model for this language")
        
        textframe = ctk.CTkTextbox(frame, font=("Calibri",12), wrap="word")
        textframe.configure(state="disabled", width=300, height=290)
        textframe.grid(row=3, column=0, sticky="nsew")
        textframe.configure(state="normal")
        textframe.insert("1.0","\n\n"+date+" - "+language)
        textframe.insert("1.0","\nTitle : "+name+"\n\n"+content)
        textframe.configure(state="disabled")
        
        
        urlbutton = ctk.CTkButton(textframe, text="Direct link", command=self.open_url, fg_color="#469d54", hover_color="#2a5c33")
        urlbutton.grid(row=3, column=0, padx=10, pady=(20,0), sticky="nsew")
        
        urlbutton = ctk.CTkButton(textframe, text="Reload window", command=lambda : self.open_toplevel(source,savename,savecontent,date,language,url,index), fg_color="#469d54", hover_color="#2a5c33")
        urlbutton.grid(row=4, column=0, padx=10, pady=(5,5), sticky="nsew")   
        
        urlbutton = ctk.CTkButton(textframe, text="Clear window", command=self.deletepack, fg_color="#469d54", hover_color="#2a5c33")
        urlbutton.grid(row=5, column=0, padx=10, pady=(0,20), sticky="nsew")            


    def clear(self):
        try:
            self.frame_buttons.grid_remove()
            self.deletepack()
        except:
            pass
    

    def deletepack(self):
        self.search_output_text2.pack_forget()  
            
    def searchgui(self):
        try:
            self.deletepack()
        except:
            pass
        self.search_output_text.configure(state='normal')
        self.search_thread = threading.Thread(target=self.search_thread_func)
        self.search_thread.start()


    def rss_thread_func(self):
        index = 0
        processed_sources = set()
                
        if self.opmlfile[0] == 'E':
            print("OPML file not defined/valid, please go to 'OPML Settings' and choose a file.")
            return 
        
        sources = opmlparser(self.opmlfile)
        
        sys.stdout = sys.__stdout__
        sys.stdout = self.rss_output_stream
        
        maximum = len(sources)
        self.progressbar['maximum'] = maximum
        
        print(f"\nParsing starting in [{self.language}] on {maximum} RSS sources...\n")
        starttime = time.time()
        for source in sources:
            progress = (index / maximum)
            self.progressbar.set(float(progress))
            index += 1
            rssparser(source, processed_sources, self.language)
        self.progressbar.set(1)
        timeelapsed = time.time() - starttime 
        print("\nParsing finished in %.2f seconds.\n" % timeelapsed)


    def rssparsergui(self):
        sys.stdout = sys.__stdout__
        sys.stdout = self.rss_output_stream
        self.rss_thread = threading.Thread(target=self.rss_thread_func)
        self.rss_thread.start()
        

    def opmladdsource_thread_func(self):
        if self.opmlfile[0] == 'E':
            self.search_output_text_url.configure(state='normal')
            self.search_output_text_url.delete('1.0', 'end')
            self.search_output_text_url.insert('1.0', "OPML file not defined/valid, please select a file via the 'OPML File' button.")
            self.opmlfile = self.opmlcheck()
            self.search_output_text_url.configure(state='disabled')
            return
        self.res = opmladd(self.opmlfile,self.title_url.get(),self.entry_url.get())
        self.search_output_text_url.configure(state='normal')
        self.search_output_text_url.delete('1.0', 'end')
        self.search_output_text_url.insert('1.0', self.res)
        self.search_output_text_url.configure(state='disabled')
        
    def opmladdsource(self):
        self.search_output_text_url.configure(state='normal')
        self.search_thread_url = threading.Thread(target=self.opmladdsource_thread_func)
        self.search_thread_url.start()
        

    def open_url(self):
        webbrowser.open(self.urlcallback)
        
    def languagetoacro(self, language):
        if language=="English":
            return "en"
        elif language=="French":
            return "fr"
        elif language=="Russian":
            return "ru"
        elif language=="Italian":
            return "it"
        elif language=="Spanish":
            return "es"
        elif language=="All":
            return "All"
        elif language=="None":
            return "None"
        return "en"
    
    def languageoption(self, value):
        self.language = self.languagetoacro(value)  
        
    def languageoptionsearch(self, value):
        self.languagesearch = self.languagetoacro(value)
        
    def languageoptiontranslation(self, value):
        self.languagetranslation = self.languagetoacro(value)   
        
    def number_outputs_func(self,value):
        self.number_outputs = int(value)
        
    def dateoptionfilter(self, value):
        self.dateoption = value
        if self.dateoption != "All":
            self.dateoption = int(self.dateoption.split(" ")[1])
            
    def get_path(self, event):
        self.pathLabel.configure(text = event.data)
        data = str(event.data).replace("{", "").replace("}", "")
        data = "data"+data.split("data")[1]
        print("--",data,"--")
        verify = data.split(".")
        if verify[-1] == "opml":
            opml_data = {"opmlpath": data}
            with open("data/data.json", "w") as f:
                json.dump(opml_data, f)
        else:
            print("Wrong file extension.")
        
    def opmlchoice(self):
        self.root = Tk()
        self.root.geometry("750x200")
        self.root.title("Get file path")

        self.pathLabel = ctk.CTkLabel(self.root, text="Drag and drop file in the entry box")
        self.pathLabel.pack(side=TOP, pady=10)
        
        entryWidget = ctk.CTkEntry(self.root)
        entryWidget.pack(side=TOP, padx=5, pady=5)

        entryWidget.drop_target_register(DND_ALL)
        entryWidget.dnd_bind("<<Drop>>", self.get_path)
        
        
        
        button = ctk.CTkButton(self.root, text="Finish", command=self.root.destroy, fg_color="#469d54", hover_color="#2a5c33")
        button.pack(pady=(20,5))


        self.root.mainloop()
        

    def validate_opml(self, file_path):
        if os.path.exists(file_path):
            return True
        else:
            return False

    def opmlcheck(self):
        if os.path.exists('data/data.json'):
            with open('data/data.json') as f:
                data = f.read()
                if data:
                    data = json.loads(data)
                    if 'opmlpath' in data:
                        if self.validate_opml(data['opmlpath']):
                            return data['opmlpath']
                        return "Error: OPML file seems to be invalid."
                    else:
                        return 'Error: opmlpath not found in data.json'
                else:
                    return 'Error: data.json is empty'
        else:
            return 'Error: data.json not found'
    


if __name__ == "__main__":
    app = App()
    app.mainloop()