from flask import Flask, request
from flask_restful import reqparse, abort, Api, Resource
from konlpy.tag import Okt
from datetime import datetime, timedelta

okt = Okt()
app = Flask(__name__)
api = Api(app)
# 받는 파라미터
parser = reqparse.RequestParser()

# 분석
class Analyst(Resource):

    def post(self):
        args = parser.parse_args()

        # chats file 받기
        chats = request.files['file']

        # 학습 Thread 돌리기

        return self.analyst(chats)

    def analyst(self, chats):
        # 대화 상대 이름
        opponent = chats.readline().decode('utf-8').split()[0]

        # list로 변경
        chats = self.convert_list(chats)

        # 단어 빈도수 세기
        my_chat, opponent_chat = self.count_word(chats, opponent)

        # 씹힘 세기
        ignore_cnt = self.count_ignore(chats)

        # 시간대별로 세기
        time_slot_cnt = self.count_time_slot(chats)

        # 답장 빈도 세기

        # return my_chat, opponent_chat, 201

    def count_word(self, chats, opponent): # chat 안에 있는 단어 세기

        opponent_chat = {}
        my_chat = {}

        for chat in chats:
            chat_split = chat.split(" : ")

            if len(chat_split) == 1:
                continue

            tmp = opponent_chat if opponent in chat_split[0] else my_chat
            for word in okt.nouns(chat_split[1][1::]):
                tmp[word] = tmp.get(word, 0) + 1

        return my_chat, opponent_chat

    def convert_list(self, chats):
        chat_list = []
        # 저장한 날짜 날리기
        chats.readline().decode('utf-8')
        chat = chats.readline().decode('utf-8')
        while chat:
            chat_list.append(chat)
            chat = chats.readline().decode('utf-8')
        return chat_list

    def count_ignore(self, chats):

        before = None
        curr = 0

        cnt = 0
        for chat in chats:

            # 날짜 - 메세지 추출
            chat_split = chat.split(" : ")

            # 날짜만 제외
            if len(chat_split) == 1:
                continue

            dt = self.get_datetime(chat_split)
            curr = datetime(dt[0], dt[1], dt[2], dt[3], dt[4])

            if not before:
                before = curr
                continue
            else:
                # 비교해서 얼만큼 차이일 때 무시한걸로 칠건지 계싼
                print(curr - before)

        return cnt

    def count_time_slot(chats, minute_interval):
        time_slot_cnt = {}

        for chat in chats:

            # 날짜 - 메세지 추출
            chat_split = chat.split(" : ")

            # 날짜만 제외
            if len(chat_split) == 1:
                continue

            # 날짜 얻기
            year, month, day, hour, minute = self.get_datetime(chat_split)

            # interval에 따라 이 시간에 맞는 시간대 정하기
            remainder = (60 * hour + minute) % minute_interval
            slot_h_m = ()
            # 현재 시간보다 이른 시간대의 경우
            if remainder < (minute_interval / 2):
                slot_minute = minute - remainder
                if slot_minute < 0:
                    slot_minute = 60 - slot_minute
                    hour -= 1
                slot_h_m = (hour, slot_minute)
            # 현재 시간보다 나중 시간대의 경우
            else:
                slot_minute = minute - remainder + minute_interval
                hour += slot_minute // 60
                slot_minute %= 60
                slot_h_m = (hour, slot_minute)

            """
            # dictionary에 넣기
            try:
                # list에 추가
                time_slot_cnt[slot_h_m].append(chat_split[1])
            except KeyError as ke:
                # dictionary에 없으면 list를 추가
                time_slot_cnt[slot_h_m] = [chat_split[1]]
            """

            # dictionary에 카운트하기
            try:
                # 해당 slot의 카운트 증가
                time_slot_cnt[slot_h_m] += 1
            except KeyError as ke:
                # dictionary에 없으면 값 추가
                time_slot_cnt[slot_h_m] = 1

        return time_slot_cnt

    def get_datetime(self, chat):
        tmp = chat[0].split("년")
        year = tmp[0]
        tmp = tmp[1]

        tmp = tmp.split("월")
        month = tmp[0]
        tmp = tmp[1]

        tmp = tmp.split("일")
        day = tmp[0]
        tmp = tmp[1]

        tmp = tmp.split(":")
        minute = tmp[1][0:2]
        tmp = tmp[0]
        hour = 0
        if "오전" in tmp:
            hour = int(tmp.split("오전")[1])
            hour = 0 if hour == 12 else hour
        else:
            hour = int(tmp.split("오후")[1]) + 12
            hour = 12 if hour == 24 else hour

        return int(year), int(month), int(day), hour, int(minute)

# URL router 에 맵핑한다.(Rest URL 정의)
api.add_resource(Analyst, '/analyze')

# 서버 실행
if __name__ == '__main__':
    app.run(debug=True)
