# Monitoring of SMA Sunny Tripower and SMA Sunny Island
# via Modbus Protokoll

param( 
	[string] $remoteHost = "enter IPs below!!", 
	[int]$port = 502
) 

function modbusread ([string]$remoteHost, [int]$port, [int]$startaddress,[int]$bytecount,[string]$signed) {

    write-host "Reading Register #$startaddress"

    # Build Request Data

	[byte[]]$sendbuffer=00,110  # Transaction Identifier
	$sendbuffer+=00,00			#Protocol identifier
	$sendbuffer+=00,06			#Length
	$sendbuffer+=03				#Unit ID
	$sendbuffer+=04				#Function Read Input Registers
	$sendbuffer+=[byte]([math]::Truncate(($startaddress)/256)),([system.byte](($startaddress)%256))		
	$sendbuffer+=00,($bytecount)

    # Send Request Data

	$tcpclient = new-object System.Net.Sockets.TcpClient($remoteHost, $port) 
	$netStream  = $tcpclient.GetStream() 
	$netStream.write($sendbuffer,0,$sendbuffer.length)
	start-sleep -milliseconds 50

    # Receive Data

	[byte[]]$recbuffer = new-object System.Byte[] ([int]($bytecount+9)) 
	$receivedbytes = $netStream.Read($recbuffer, 0, [int]($bytecount+9));
	$netStream.Close() 
	$tcpclient.Close() 

    # Process Data

	$resultdata = $recbuffer[9..($recbuffer[8]+8)]

    [byte[]] $bytes = $resultdata[3],$resultdata[2],$resultdata[1],$resultdata[0] # need to reverse byte order

    if ($signed -eq "signed")    {
        $result=[bitconverter]::ToInt32($bytes,0);
        write-host  "Received int=" $result
    }
    else     {
        $result=[bitconverter]::ToUInt32($bytes,0);
        write-host  "Received  uint=" $result
    }
    $result
}

# Process One Dataset

function onedataset([string]$name, [int]$theid, [string]$unit, [int]$divider, [string]$type,[string]$signed) {
    write-host "==== $name ===="
    $value=((modbusread $remoteHost $port ($theid) 4 $signed)/$divider)
    if ($value -eq 4294967295 -Or$value -eq 2147483648  -Or $value -eq  -2147483648)
        { $value=0 }
            "    <result>`r`n"
            "        <channel>"+$name+"</channel>`r`n"
            "        <customunit>"+$unit+"</customunit>`r`n"
            "        <value>"+($value/$divider)+"</value>`r`n"
            "        <float>1</float>`r`n"
            "        <mode>"+$type+"</mode><SpeedTime>Hour</SpeedTime>`r`n"
            "    </result>`r`n"
        }
    

# Main code

write-host "Let's go..."
[string]$prtgresult=""
$prtgresult+="<?xml version=""1.0"" encoding=""Windows-1252"" ?>`r`n"
$prtgresult+="<prtg>`r`n"
[bool]$errorfound = $false


try {

    $remoteHost = "192.168.142.165" # Let's look at the Battery System SMA Sunny Island

    $prtgresult+=onedataset "Power from Grid" 30865 "W" 1 "Absolute" "signed"
    $prtgresult+=onedataset "Power from Battery" 30775 "W" 1 "Absolute" "signed"
    $prtgresult+=onedataset "Power to Grid" 30867 "W" 1 "Absolute" "signed" 

    $prtgresult+=onedataset "Battery Charge" 30845 "%" 1 "Absolute"
    $prtgresult+=onedataset "Battery Current" 30843 "A" 1 "Absolute" "signed"
    
    $status=(modbusread $remoteHost $port (30201) 4)
    switch ($status) {
        "35"	{$prtgresult+="<text>Status: Error</text><error>Status: Fehler</error>`r`n"}
        "303"	{$prtgresult+="<text>Status: Off</text>`r`n"}
        "307"	{$prtgresult+="<text>Status: OK</text>`r`n"}
        "455"	{$prtgresult+="<text>Status: Warning</text>`r`n"}
    }

    $remoteHost = "192.168.142.166" # Let's look at the PV System SMA Sunny Tripower


    $prtgresult+=onedataset "Power from PV" 30775 "W" 1 "Absolute" "signed"
    $prtgresult+=onedataset "Solar Energy Total" 30529 "Wh" 1 "Absolute"
    $prtgresult+=onedataset "Solar Energy Today" 30535 "Wh" 1 "Absolute"

    $prtgresult+="</prtg>"
}
catch {
	write-host "Unable to Connect and retrieve data $_.Exception.Message"
	$prtgresult+="   <error>2</error>`r`n"
	$prtgresult+="   <text>Unable to Connect and retrieve data  "+($_.Exception.Message +" at "+ $_.InvocationInfo.PositionMessage)+"</text>`r`n"
    $prtgresult+="</prtg>"
	$errorfound = $true
}

if ($errorfound) {
	write-host "Error Found. Ending with EXIT Code" ($prtgresult).prtg.error
}
write-host "Sending PRTGRESULT to STDOUT"
$prtgresult
