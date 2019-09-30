from __future__ import absolute_import
import logging
from rest_framework import serializers
from .internal import validate_app_ids, validate_char_limit

log = logging.getLogger(__name__)


class Obj(object):
    def __init__(self, data):
        self.__dict__.update(data)


class BaseASKSerializer(serializers.Serializer):
    def create(self, validated_data):
        return Obj(data=validated_data)


class ASKApplicationSerializer(BaseASKSerializer):
    applicationId = serializers.CharField(validators=[validate_app_ids])


class ASKUserSerializer(BaseASKSerializer):
    userId = serializers.CharField()
    accessToken = serializers.CharField(required=False, allow_null=True)


class ASKSessionSerializer(BaseASKSerializer):
    sessionId = serializers.CharField()
    application = ASKApplicationSerializer()
    attributes = serializers.DictField(required=False, allow_null=True)
    user = ASKUserSerializer()
    new = serializers.BooleanField()


class ASKIntentSerializer(BaseASKSerializer):
    name = serializers.CharField()
    slots = serializers.DictField(required=False, allow_null=True)


class ASKRequestSerializer(BaseASKSerializer):
    type = serializers.CharField()
    requestId = serializers.CharField()
    timestamp = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    intent = ASKIntentSerializer(required=False)
    reason = serializers.CharField(required=False)
    message = serializers.DictField(required=False)

class AskSystemSerializer(BaseASKSerializer):
    apiAccessToken = serializers.CharField()
    application = ASKApplicationSerializer()

class ASKContextSerializer(BaseASKSerializer):
    System = AskSystemSerializer()

class ASKOutputSpeechSerializer(BaseASKSerializer):
    # TODO: Choice validation to check if text and ssml are not both empty
    type = serializers.ChoiceField(choices=("PlainText", "SSML"))
    text = serializers.CharField(required=False)
    ssml = serializers.CharField(required=False)


class ASKCardSerializer(BaseASKSerializer):
    type = serializers.ChoiceField(default="Simple", choices=("Simple", "LinkAccount"))
    title = serializers.CharField(required=False)
    content = serializers.CharField(required=False)


class ASKRepromptSerializer(BaseASKSerializer):
    outputSpeech = ASKOutputSpeechSerializer(required=False)


class ASKResponseSerializer(BaseASKSerializer):
    outputSpeech = ASKOutputSpeechSerializer(
        required=False, validators=[validate_char_limit]
    )
    card = ASKCardSerializer(required=False, validators=[validate_char_limit])
    reprompt = ASKRepromptSerializer(required=False)
    shouldEndSession = serializers.BooleanField()


class ASKInputSerializer(BaseASKSerializer):
    version = serializers.FloatField(required=True)
    session = ASKSessionSerializer(required=False)
    request = ASKRequestSerializer()
    context = ASKContextSerializer()

    def validate(self, data):
        if not data.get('session'):
            if data.get('request', {}).get('type') == 'Messaging.MessageReceived':
                # we need a session, but this out-of-session request type does not have one so copy from the context
                data['session'] = {'application' : data['context']['System']['application'].copy()}
            else:
                raise serializers.ValidationError("Session field is required")
        return data

class ASKOutputSerializer(BaseASKSerializer):
    version = serializers.FloatField(required=True)
    sessionAttributes = serializers.DictField(required=False)
    response = ASKResponseSerializer()
