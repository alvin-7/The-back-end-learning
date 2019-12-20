



## 安装C++环境

### 先决条件

1. 安装 `Visual Studio Code`
2. 安装 `C++ extension for VS Code`
3. 安装 `Mingw-w64` 到文件夹中，假定我们安装到 `C:\Mingw-w64`
4. 添加 `Mingw-w64` bin 文件夹到 Windows Path 环境变量中
   1. 打开 `Windows Setting` 然后 进入 `系统属性 - 高级 - 环境变量 - 系统变量 - Path`
   2. 新建一个环境变量 如 `c:\mingw-w64\x86_64-8.1.0-win32-seh-rt_v6-rev0\mingw64\bin`
   3. 确定并保存到`Path`中，你需要打开控制台让新的环境变量生效

### 创建一个工作区

1. 按 `Ctrl + Shift + P` 打開命令面板，输入`C++`，选择 `Edit configurations(UI)`

2. 將**IntelliSense模式**設置為`gcc-x64`

3. 直接编辑 `c_cpp_properties.json`

4. ```json
   {
     "configurations": [
       {
         "name": "Win32",
         "includePath": ["${workspaceFolder}/**", "${vcpkgRoot}/x86-windows/include"],
         "defines": ["_DEBUG", "UNICODE", "_UNICODE"],
         "windowsSdkVersion": "10.0.17763.0",
         "compilerPath": "C:\\mingw-w64\\x86_64-8.1.0-win32-seh-rt_v6-rev0\\mingw64\\bin\\g++.exe",
         "cStandard": "c11",
         "cppStandard": "c++17",
         "intelliSenseMode": "${default}"
       }
     ],
     "version": 4
   }
   ```

### 创建一个构建任务

1. 在 `.vscode` 目录下创建一个 `tasks.json` 文件

2. 编辑

3. ```json
   {
       // See https://go.microsoft.com/fwlink/?LinkId=733558
       // for the documentation about the tasks.json format
       "version": "2.0.0",
       "tasks": [
           {
               "label": "Build",
               "command": "g++",
               "args": [
                   "-g",
                   "-Wall",
                   "-std=c++11",
                   "-lm",
                   "${file}",
                   "-o",
                   "${fileDirname}/${fileBasenameNoExtension}.o"
               ],
               "windows": {
                   "args": [
                       "-g",
                       "-Wall",
                       "-std=c++11",
                       "-lm",
                       "${file}",
                       "-o",
                       "${fileDirname}/${fileBasenameNoExtension}.exe"
                   ]
               },
               "presentation": {
                   "reveal": "always",
                   "echo": false,
                   "focus": true
               },
               "problemMatcher": {
                   "owner": "cpp",
                   "fileLocation": "absolute",
                   "pattern": {
                       "regexp": "^(.*):(\\d+):(\\d+):\\s+(error):\\s+(.*)$",
                       "file": 1,
                       "line": 2,
                       "column": 3,
                       "severity": 4,
                       "message": 5
                   }
               }
           },
           {
               "label": "Run",
               "type": "shell",
               "dependsOn": "Build",
               "command": "${fileDirname}/${fileBasenameNoExtension}.o",
               "windows": {
                   "command": "${fileDirname}/${fileBasenameNoExtension}.exe"
               },
               "args": [],
               "presentation": {
                   "reveal": "always",
                   "focus": true
               },
               "problemMatcher": [],
               "group": {
                   "kind": "test",
                   "isDefault": true
               }
           }
       ]
   }
   ```

4. 該`command`設置指定要運行的程序；在這種情況下，它就是g ++.exe。該`args`數組指定將傳遞給g ++的命令行參數。必須按照編譯器期望的順序指定這些參數。

   該`label`值就是您將在VS Code命令面板中看到的值；您可以隨意命名。

   對像中的`"isDefault": true`值`group`指定當您按Ctrl + Shift + B時將運行此任務。此屬性僅出於方便起見；如果將其設置為false，則必須從“ **運行構建任務”**下的**“**命令面板”菜單中運行它。

### 配置调试设置

>  接下來，我們將配置VS Code以在您按F5鍵時啟動GCC調試器（gdb.exe）

1. 在命令面板中，输入`launch`，然后选择`调试`：打开`launch.json`。 接下来，选择`GDB/LLDB`环境

2. 上面如果不行，可以点击调试，选择 `GDB/LLDB`环境，然后点击配置就可以打开`launch.json`文件

3. 修改`launch.json`文件

4. ```json
   {
       // Use IntelliSense to learn about possible attributes.
       // Hover to view descriptions of existing attributes.
       // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
       "version": "0.2.0",
       "configurations": [
   
           {
               "name": "c++ Launch", //配置文件的名字.因为一个launch里可以有好几个配置文件
               "type": "cppdbg",
               "request": "launch",
               "program": "${fileDirname}/${fileBasenameNoExtension}.exe",
               "args": [],
               "stopAtEntry": false,
               "cwd": "${workspaceFolder}",
               "environment": [],
               "externalConsole": true,
               "MIMode": "gdb",
               "miDebuggerPath": "C:\\Program Files\\mingw-w64\\mingw64\\bin\\gdb.exe",//调试器的位置
               "setupCommands": [
                   {
                       "description": "Enable pretty-printing for gdb",
                       "text": "-enable-pretty-printing",
                       "ignoreFailures": true
                   }
               ],
               "preLaunchTask": "Build"
           }
       ]
   }
   ```

5. 此时，按`Ctrl+Shift+B`，运行`helloworld.cpp` 