Option Explicit

' Runs one batch file without opening a command-prompt window.  The task waits
' for completion, so Task Scheduler still records the batch file's exit code.
If WScript.Arguments.Count <> 1 Then
    WScript.Quit 87
End If

Dim batchPath, fso, shell, command, exitCode
batchPath = WScript.Arguments(0)

Set fso = CreateObject("Scripting.FileSystemObject")
If Not fso.FileExists(batchPath) Then
    WScript.Quit 2
End If

Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = fso.GetParentFolderName(batchPath)
command = Chr(34) & shell.ExpandEnvironmentStrings("%ComSpec%") & Chr(34) _
    & " /c " & Chr(34) & batchPath & Chr(34)
exitCode = shell.Run(command, 0, True)
WScript.Quit exitCode
