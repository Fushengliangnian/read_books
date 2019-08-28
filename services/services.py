# -*- coding: utf-8 -*-
# !/usr/bin/env python
# @Time    : 2019-08-28 11:00
# @Author  : lidong@immusician.com
# @Site    :
# @File    : services.py
from copy import deepcopy

import ujson
from bson import ObjectId

from . import BaseService


class ABTestingService(BaseService):
    def __init__(self, services):
        super(ABTestingService, self).__init__(services)
        self.indicator_coll = self.mongo_conn.indicator_coll
        self.project_indicator_coll = self.mongo_conn.project_indicator_coll
        self.event_coll = self.mongo_conn.event_coll
        self.event_info_coll = self.mongo_conn.event_info_coll

    def _count(self, select_args, collection):
        total = self.mongo_conn.db[collection].count(select_args)
        return total

    def compute_total(self, select_args, collection):
        total = self._count(select_args, collection)
        return "total", total

    def _aggregation(self, collection, pipeline):
        result = self.mongo_conn.db[collection].aggregate(pipeline)
        return list(result)

    def aggregation_by_user(self, select_args, collection):
        query = {"$match": select_args}
        group = {"$group": {"_id": "$uid"}}
        result = self._aggregation(collection, [query, group])
        return "total_by_user", len(result)

    def aggr_course_by_event_id_and_uid(self, select_args, collection):
        query = {"$match": select_args}
        group = {"$group": {
            "_id": "$item_id",
            "total": {"$sum": 1},
            "first_click_time": {"$min": "$create_time"},
            "last_click_time": {"$max": "$create_time"}
        }}
        result = self._aggregation(collection, [query, group])
        return "course_by_aggregation", result


class EventService(ABTestingService):

    def save_event_info_multi(self, even_info_list):
        insert_data = []
        for even_info in even_info_list:
            insert_data.append(even_info.to_doc())

        self.event_info_coll.insert(insert_data)
        return self

    def save_event_info_single(self, event_obj):
        self.event_info_coll.insert_one(event_obj.to_doc())
        return self

    def get_event(self):
        cursor = self.event_coll.find()

        return [ABTestingEventModel.from_doc(doc) for doc in cursor]

    _field_validate = ["item_id", "event_id", "create_time", "uid", "item_type", "duration", "other"]

    def validate_event_need_params(self, event_need_params):
        _keys = []
        for key, value in event_need_params.items():
            if "required" not in value:
                raise APIValueError(value, message="{} 中必须包含 required".format(value))
            if "value_type" not in value:
                raise APIValueError(value, message="{} 中必须包含 value_type".format(value))
            if "description" not in value:
                raise APIValueError(value, message="{} 中必须包含 description".format(value))
            if key not in self._field_validate:
                raise APIValueError(value, message="{} 中不可存在 {}".format(value, key))
            _keys.append(key)

        if len(self._field_validate) > len(_keys) + 1:
            raise APIValueError(_keys, message="值的格式错误")

    def create_event(self, args):
        event_name = args["event_name"]
        cursor = self.event_coll.find_one({"event_name": event_name})
        if cursor:
            event_id = str(cursor["_id"])
            raise APIBusinessError({"id": event_id, "event_name": event_name}, message="{} 该事件已存在".format(event_name))

        doc = ABTestingEventModel(**args).to_doc()
        self.event_coll.insert_one(doc)
        inserted_id = doc.pop("_id")
        doc["id"] = str(inserted_id)
        return doc


class ABTestingProjectService(ABTestingService):

    def _check_field(self, params):
        for param in params:
            indicator_id = param["indicator_id"]
            indicator = self.indicator_coll.find_one({"_id": ObjectId(indicator_id)})
            select_args = indicator["select_args"]
            for key, args in select_args.items():
                value = param.get(key, None)
                value_str_type = args["value_type"]
                value_type = self.field_type[value_str_type]
                required = args["required"]
                if not required and value is None:
                    value = args["default"]
                    param[key] = value

                if required and not value:
                    raise APIValueError(value, message="{} 的值是必填的".format(key))

                if value_str_type == "bool":
                    value = int(value)
                    if value == 1 or value == 0:
                        value = bool(value)
                        param[key] = value
                    else:
                        raise APIValueError(value, message="{} 值的类型必须是 int 且必须是 0 或 1".format(value))

                if value_str_type == "int":
                    value = int(value)

                if not isinstance(value, value_type):
                    raise APIValueError(value, message="{} 值的类型必须是 {}".format(value, value_type))

    @staticmethod
    def _result_data(data):
        if "compute_ratio" in data:
            return
        if len(data) == 1:
            data["compute_ratio"] = data[0].values()[0]

    def _get_uid_list(self, user_group):
        # TODO:
        return [38, 40, 55, 53, 44, 86, 70, 99]

    @staticmethod
    def _update_query_uid_and_time(select_args, uid_list, param, args):
        if not select_args.get("uid"):
            if uid_list:
                select_args["uid"] = {"$in": uid_list}
        start_time = param.get("start_time")
        end_time = param.get("end_time")

        if len(args) >= 1 and start_time and end_time:
            select_args[args[0]] = {"$gte": start_time, "$lte": end_time}

        return select_args

    def _exe_need_way(self, indicator, indicator_select_args, param):
        collection = ""
        uid_list = []
        data = {}

        if "collection_name" in indicator:
            collection = indicator.pop("collection_name")

        if "user_group" in indicator_select_args:
            user_group = indicator_select_args.pop("user_group")
            uid_list = self._get_uid_list(user_group)
            uid_list = []

        for way, args in indicator["need_way"].items():
            select_args = self._update_query_uid_and_time(indicator_select_args, uid_list, param, args)
            k, v = getattr(self, way)(select_args, collection)
            data[k] = v

        self._show_data(data, indicator["show_data"])
        return data

    def _show_data(self, primitive_data, show_rule):
        for k, v in show_rule.items():
            if ":" in v:
                a, b = v.split(":")
                v = primitive_data.pop(a).get(b)
                primitive_data[k] = v
            else:
                primitive_data[k] = primitive_data.pop(v)

    field_type = {"int": int, "str": str, "bool": bool}

    def _save_redis(self, key, value, pro_id, param):
        item = self.redis_conn.hget(key, value)
        if item:
            item = ujson.loads(item)
            item["project_info"].append({"id": str(pro_id), "name": param["name"]})
            self.redis_conn.hset(key, value, ujson.dumps(item))
            return False
        return True

    def _get_redis(self, key):
        items = self.redis_conn.hgetall(key)
        if items:
            items = sorted(items.values(), key=lambda x: ujson.loads(x)["order"])
            return [ujson.loads(item) for item in items]

    def create_project(self, param):
        ratio_indicator_list = param["ratio_indicator_list"]
        self._check_field(ratio_indicator_list)
        indicator_select_args_list = param["indicator_select_args_list"]
        # self._check_field(indicator_select_args_dict.values())
        self._check_field(indicator_select_args_list)
        cursor = self.project_indicator_coll.insert_one(param)
        pro_id = cursor.inserted_id

        activity_name = param["activity_name"]
        if activity_name:
            key = "ai_ab_testing_activity"
            value = activity_name
            is_create = self._save_redis(key, value, pro_id, param)
            if is_create:
                self.create_activity(activity_name, [{"id": str(pro_id), "name": param["name"]}])
        else:
            key = "ai_ab_testing_course"
            value = param["course_id"]

            is_create = self._save_redis(key, value, pro_id, param)
            if is_create:
                self.create_course(param["course_id"], param["course_name"],
                                   [{"id": str(pro_id), "name": param["name"]}])

    def get_project_data(self, project_indicator_id, param):
        project = self.project_indicator_coll.find_one({"_id": ObjectId(project_indicator_id)})
        has_ratio = project["has_ratio"]
        indicator_select_args_list = project["indicator_select_args_list"]
        data = {}

        # 循环执行正常指标所需要的方法
        for index, indicator_select_args in enumerate(indicator_select_args_list):
            indicator = self.services.ab_testing_indicator_service.find_one(indicator_select_args)
            result = self._exe_need_way(indicator, indicator_select_args, param)
            data[index] = result

        # 判断是否存在比率指标, 并去执行
        if has_ratio:
            ratio_indicator_list = project["ratio_indicator_list"]
            for ratio_indicator_select_args_dict in ratio_indicator_list:
                ratio_indicator = self.services.ab_testing_indicator_service.find_one(ratio_indicator_select_args_dict)
                result = self._exe_need_way(ratio_indicator, ratio_indicator_select_args_dict, data)
                data.update(result)

        self._result_data(data)

        return data

    def get_data_by_interaction(self, project_indicator_id, param):
        project = self.project_indicator_coll.find_one({"_id": ObjectId(project_indicator_id)})
        indicator_select_args_list = project["indicator_select_args_list"]
        data = {}

        for index, indicator_select_args in enumerate(indicator_select_args_list):
            if index is not 0:
                indicator_select_args[index - 1] = data[index - 1]
            indicator = self.services.ab_testing_indicator_service.find_one(indicator_select_args)
            result = self._exe_need_way(indicator, indicator_select_args, param)
            data[index] = result

    def get_course(self):
        courses = self._get_redis("ai_ab_testing_course")
        if courses:
            return courses

        pipeline = [
            {"$group": {"_id": "$course_id", "project_ids": {"$addToSet": "$_id"}, "names": {"$addToSet": "$name"}}}
        ]
        cursor = self.project_indicator_coll.aggregate(pipeline)
        if not cursor:
            return {}
        data = []
        query_course = []
        for item in cursor:
            if not item["_id"]:
                continue
            project_ids = item["project_ids"]
            names = item["names"]
            item_id = item["_id"]
            project_info = [{"id": str(_id), "name": names[index]} for index, _id in enumerate(project_ids)]
            data.append({"course_id": item_id, "project_info": project_info})
            query_course.append(item_id)

        if not data:
            return []

        cursor = self.services.course_service.find_many(size=len(data), **{"_id": {"$in": query_course}})
        course_dict = {course.id: course.name for course in cursor}
        for item in data:
            item["course_name"] = course_dict[item["course_id"]]
        redis_data = deepcopy(data)
        redis_dict = {}
        for index, item in enumerate(redis_data):
            item["order"] = index
            redis_dict[item["course_id"]] = ujson.dumps(item)
        self.redis_conn.hmset("ai_ab_testing_course", redis_dict)
        return data

    def get_activity(self):
        activity = self._get_redis("ai_ab_testing_activity")
        if activity:
            return activity

        pipeline = [
            {"$group": {"_id": "$activity_name", "project_ids": {"$addToSet": "$_id"}, "names": {"$addToSet": "$name"}}}
        ]
        cursor = self.project_indicator_coll.aggregate(pipeline)
        if not cursor:
            return []

        data = []
        for item in cursor:
            if not item["_id"]:
                continue
            project_ids = item["project_ids"]
            names = item["names"]
            item_id = item["_id"]
            project_info = [{"id": str(_id), "name": names[index]} for index, _id in enumerate(project_ids)]
            data.append({"activity_name": item_id, "project_info": project_info})

        if not data:
            return []

        redis_data = deepcopy(data)
        redis_dict = {}
        for index, item in enumerate(redis_data):
            item["order"] = index
            redis_dict[item["activity_name"]] = ujson.dumps(item)
        self.redis_conn.hmset("ai_ab_testing_activity", redis_dict)
        return data

    def create_course(self, course_id, course_name, project_info=None):
        count = self.redis_conn.hlen("ai_ab_testing_course")
        self.redis_conn.hset("ai_ab_testing_course", course_id, ujson.dumps({
            "course_id": course_id,
            "course_name": course_name,
            "project_info": [] if project_info is None else project_info,
            "order": count}))

    def create_activity(self, activity_name, project_info=None):
        count = self.redis_conn.hlen("ai_ab_testing_activity")
        self.redis_conn.hset("ai_ab_testing_activity", activity_name, ujson.dumps({
            "activity_name": activity_name,
            "project_info": [] if project_info is None else project_info,
            "order": count}))

    def get_item_list(self, item_type):
        coll_name = ABTESTING_EVENT_TYPE[item_type][1]
        coll = getattr(self.mongo_conn, coll_name)
        cursor = coll.find()
        data = []
        for item in cursor:
            _id = item["_id"]
            if isinstance(_id, ObjectId):
                item["_id"] = str(_id)
            data.append(item)
        return data


class ABTestingIndicatorService(ABTestingService):

    def create_indicator(self, params):
        doc = ABTestingIndicatorModel(**params).to_doc()
        cursor = self.indicator_coll.find_one({"name": doc["name"]})
        if cursor:
            raise APIBusinessError(field={"_id": str(cursor["_id"])}, message="该事件已经存在")
        self.indicator_coll.insert_one(doc)
        doc["_id"] = str(doc["_id"])
        return doc

    def find_one(self, indicator_select_args):
        indicator_id = indicator_select_args.pop("indicator_id")
        indicator = self.indicator_coll.find_one({"_id": ObjectId(indicator_id)})
        # indicator = self.get_test_indicator(indicator_id)
        return indicator

    def find_many(self):
        cursor = self.indicator_coll.find()
        # data = [ABTestingIndicatorModel.from_doc(doc) for doc in cursor]
        return cursor

    def get_select_arg_every_list(self):
        data = []
        cursor = self.find_many()
        for item in cursor:
            indicator = ABTestingIndicatorModel.from_doc(item)
            select_args = indicator.select_args
            for key, value in select_args.items():
                is_show_list = value.get("is_show_list")
                if not is_show_list:
                    continue
                item_type = value["item_type"]
                select_list = self.services.ab_testing_project_service.get_item_list(item_type)
                value["select_list"] = select_list
                select_args[key] = value
            indicator.select_args = select_args
            data.append(indicator)
        return data
