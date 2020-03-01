# Überwachung einer AIT Wärmepumpe mit PRTG 
# via Modbus Protokoll

param( 
	[string] $remoteHost = "192.168.142.27", 
	[int]$port = 502
) 


function modbusread ([string]$remoteHost, [int]$port, [int]$startaddress,[int]$bytecount,[string]$targetformat,[string]$flipoption) {

	[byte[]]$sendbuffer=00,110  # Transaction Identifier
	$sendbuffer+=00,00			#Protocol identifier
	$sendbuffer+=00,06			#Length
	$sendbuffer+=00				#Unit ID
	$sendbuffer+=04				#Function Read Input Registers
	$sendbuffer+=[byte]([math]::Truncate(($startaddress -40001)/256)),([system.byte](($startaddress -40001)%256))		
	$sendbuffer+=00,($bytecount)
	$tcpclient = new-object System.Net.Sockets.TcpClient($remoteHost, $port) 
	$netStream  = $tcpclient.GetStream() 
	$netStream.write($sendbuffer,0,$sendbuffer.length)
	start-sleep -milliseconds 50
	[byte[]]$recbuffer = new-object System.Byte[] ([int]($bytecount+9)) 
	$receivedbytes = $netStream.Read($recbuffer, 0, [int]($bytecount+9));
	$tcpclient.Close() 
	$netStream.Close() 
	$resultdata = $recbuffer[9..($recbuffer[8]+8)]
	$resultdataflip = $resultdata.clone()
	for ($count=0; $count -lt $resultdata.length ;$count+=2) {
		$resultdataflip[$count] = $resultdata[$count+1]
		$resultdataflip[$count+1] = $resultdata[$count]
	}
	$resultdata = $resultdataflip
    [bitconverter]::ToInt16($resultdata,0)
}

write-host "Let's go..."
[string]$prtgresult=""
$prtgresult+="<?xml version=""1.0"" encoding=""Windows-1252"" ?>`r`n"
$prtgresult+="<prtg>`r`n"
[bool]$errorfound = $false

function onedataset([string]$name, [int]$theid, [string]$unit, [int]$divider) {
    "    <result>`r`n"
    "        <channel>"+$name+"</channel>`r`n"
    "        <customunit>"+$unit+"</customunit>`r`n"
    "        <value>"+((modbusread $remoteHost $port (40001+$theid) 2 int16 flip)/$divider)+"</value>`r`n"
    "        <float>1</float>`r`n"
    "        <mode>Absolute</mode>`r`n"
    "    </result>`r`n"
    }

function tworegisterdataset([string]$name, [int]$theid, [string]$unit, [int]$divider) {
    "    <result>`r`n"
    "        <channel>"+$name+"</channel>`r`n"
    "        <customunit>"+$unit+"</customunit>`r`n"
    "        <value>"+(((modbusread $remoteHost $port (40001+$theid) 2 int16 flip)*65536+(modbusread $remoteHost $port (40001+$theid+1) 2 int16 flip))/$divider)+"</value>`r`n"
    "        <float>1</float>`r`n"
    "        <mode>Absolute</mode>`r`n"
    "    </result>`r`n"
    }

try {
    $prtgresult+=onedataset "Vorlauf" 1 "&#176; C" 10
    $prtgresult+=onedataset "Ruecklauf" 2 "&#176; C" 10
    $prtgresult+=onedataset "Temperatur Aussen" 0 "&#176; C" 10
    $prtgresult+=onedataset "External Return" 3 "&#176; C" 10
    $prtgresult+=onedataset "Warmwasser" 4 "&#176; C" 10
    $prtgresult+=onedataset "Mischkreis 1" 5 "&#176; C" 10
    $prtgresult+=onedataset "Mischkreis 2" 6 "&#176; C" 10
    $prtgresult+=onedataset "Heat source inlet temperature" 9 "&#176; C" 10
    $prtgresult+=onedataset "Heat source outlet temperature" 10 "&#176; C" 10
    $prtgresult+=tworegisterdataset "Waerme (Zaehler)" 44 "kWh" 10
    $prtgresult+=onedataset "Status" 37 "Status" 1
    $prtgresult+="    <result>`r`n"
    $prtgresult+="        <channel>Betriebsstunden</channel>`r`n"
    $prtgresult+="        <customunit>h</customunit>`r`n"
    $prtgresult+="        <value>"+(((modbusread $remoteHost $port (40001+33) 2 int16 flip)))+"</value>`r`n"
    $prtgresult+="        <float>1</float>`r`n"
    $prtgresult+="        <mode>Difference</mode><SpeedTime>Hour</SpeedTime>`r`n"
    $prtgresult+="    </result>`r`n"
    $prtgresult+="    <result>`r`n"
    $prtgresult+="        <channel>Waerme gesamt</channel>`r`n"
    $prtgresult+="        <customunit>Wh</customunit>`r`n"
    $prtgresult+="        <value>"+(((modbusread $remoteHost $port (40001+44) 2 int16 flip)*65536+(modbusread $remoteHost $port (40001+44+1) 2 int16 flip))*100)+"</value>`r`n"
    $prtgresult+="        <float>1</float>`r`n"
    $prtgresult+="        <mode>Difference</mode><SpeedTime>Hour</SpeedTime><VolumeSize>Kilo</VolumeSize>`r`n"
    $prtgresult+="    </result>`r`n"
    $prtgresult+="    <result>`r`n"
    $prtgresult+="        <channel>Waerme Heizung</channel>`r`n"
    $prtgresult+="        <customunit>Wh</customunit>`r`n"
    $prtgresult+="        <value>"+(((modbusread $remoteHost $port (40001+38) 2 int16 flip)*65536+(modbusread $remoteHost $port (40001+38+1) 2 int16 flip))*100)+"</value>`r`n"
    $prtgresult+="        <float>1</float>`r`n"
    $prtgresult+="        <mode>Difference</mode><SpeedTime>Hour</SpeedTime><VolumeSize>Kilo</VolumeSize>`r`n"
    $prtgresult+="    </result>`r`n"
    $prtgresult+="    <result>`r`n"
    $prtgresult+="        <channel>Waerme Warmwasser</channel>`r`n"
    $prtgresult+="        <customunit>Wh</customunit>`r`n"
    $prtgresult+="        <value>"+(((modbusread $remoteHost $port (40001+40) 2 int16 flip)*65536+(modbusread $remoteHost $port (40001+40+1) 2 int16 flip))*100)+"</value>`r`n"
    $prtgresult+="        <float>1</float>`r`n"
    $prtgresult+="        <mode>Difference</mode><SpeedTime>Hour</SpeedTime><VolumeSize>Kilo</VolumeSize>`r`n"
    $prtgresult+="    </result>`r`n"

    $status=(modbusread $remoteHost $port 40038 2 int16 flip)
    switch ($status) {
        "0"	{$prtgresult+="<text>Betrieb: Haus-Heizung</text>`r`n"}
        "1"	{$prtgresult+="<text>Betrieb: Warmwasser</text>`r`n"}
        "2"	{$prtgresult+="<text>Betrieb: Pool</text>`r`n"}
        "3"	{$prtgresult+="<text>W&#228;rmepumpe steht (EVU Off)</text>`r`n"}
        "4"	{$prtgresult+="<text>Defrost</text>`r`n"}
        "5"	{$prtgresult+="<text>W&#228;rmepumpe steht</text>`r`n"}
        "6"	{$prtgresult+="<text>Externe Energiequelle</text>`r`n"}
    }
    $prtgresult+="</prtg>"
}
catch {
	write-host "Unable to Connect and retrieve data"
	$prtgresult+="   <error>2</error>`r`n"
	$prtgresult+="   <text>Unable to Connect and retrieve data</text>`r`n"
	$errorfound = $true
}

if ($errorfound) {
	write-host "Error Found. Ending with EXIT Code" ([xml]$prtgresult).prtg.error
}
write-host "Sending PRTGRESULT to STDOUT"
$prtgresult

if ($errorfound) {
	exit ([xml]$prtgresult).prtg.error
}
