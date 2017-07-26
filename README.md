# DrHibbert
![drimage](https://raw.githubusercontent.com/bthiago/DrHibbert/master/logo.png)

# Installation
(TODO)

# Tutorial
(TODO)

# Configuration 


## Google Authentication

### Environment Variables

* CACHETHQ_GOOGLE_CLIENT_ID
* CACHETHQ_GOOGLE_CLIENT_SECRET
* CACHETHQ_GOOGLE_REDIRECT_URL
* CACHETHQ_GOOGLE_ENABLED_DOMAIN


## CachetHQ Status Page

### Dr Hibbert CachetHQ Integration
* DRHIBBERT_CACHETCLIENT_TOKEN
* DRHIBBERT_CACHETCLIENT_URL

## Receiving alarms from AWS CloudWatch

### Environment Variables

#### AWS Client (Boto3)
* AWS_ACCESS_KEY_ID
* AWS_SECRET_ACCESS_KEY
* AWS_DEFAULT_REGION

#### Dr Hibbert AWS Integration 
We'll use these variables to setup components in CachetHQ:
* DRHIBBERT_AWS_TAG_MONITOR_GROUP_KEY
* DRHIBBERT_AWS_TAG_MONITOR_COMPONENT_KEY

### Endpoint Documentation
(TODO)

## Receiving alarms from New Relic

### Endpoint Documentation
(TODO)

## Creating alarms into AWS CloudWatch 

### Environment Variables

#### Dr Hibbert AWS Integration 
* DRHIBBERT_AWS_TOPICALARM : SNS Topic ARN that you need to create previously. This topic should be configured to trigger  Dr. Hibbert AWS Endpoint (Section Receiving alarms from AWS CloudWatch)
* DRHIBBERT_AWS_PREFIX_ALARM : AWS Alarm Name Prefix
* DRHIBBERT_AWS_TAG_MONITOR_GROUP_KEY : We'll use this to setup components in CachetHQ
* DRHIBBERT_AWS_TAG_MONITOR_COMPONENT_KEY : We'll use this to setup components in CachetHQ

### Endpoint Documentation
(TODO)


## Creating alarms into New Relic 

### Environment Variables

#### Dr Hibbert NewRelic Integration 
* DRHIBBERT_NEWRELICCLIENT_TOKEN
* DRHIBBERT_NEWRELICCLIENT_URL
* DRHIBBERT_NEWRELICCLIENT_CHANNEL_ID : NewRelic Channel ID that you need to create previously. This channel should be configured to trigger Dr. Hibbert NewRelic Endpoint (Section Receiving alarms from New Relic)

### Endpoint Documentation
(TODO)

